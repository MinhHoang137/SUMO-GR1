
import os
import xml.etree.ElementTree as ET

from Traffic.crossRoad import CrossRoadReader


# Fallback width (m) chỉ khi không có `<lane width>` lẫn `<type width>` cho edge.
# 3.2m = SUMO default lane width cho passenger vclass.
SUMO_DEFAULT_LANE_WIDTH = 3.2

# Khoảng cách XY tối đa để chấp nhận snap Z. Nếu lane endpoint cách polygon xa hơn ngưỡng
# này → bỏ qua snap (data bất thường, Z interpolation không đáng tin).
SNAP_MAX_DIST = 5.0


def _snap_z_to_polygon(point, polygon, max_dist=SNAP_MAX_DIST):
    """Giữ NGUYÊN XY của point, chỉ điều chỉnh Z (cao độ) bám theo cạnh polygon
    junction gần nhất (project XY xuống cạnh, nội suy Z dọc cạnh đó).

    Lý do bỏ snap XY:
      * Lane sidewalk có centerline OFFSET ra ngoài polygon junction (polygon bao phần
        đường xe, không bao vỉa hè). Snap XY kéo endpoint vào trong → mesh ngắn lại
        trong khi pedestrian sim đi theo path SUMO gốc → "lơ lửng" ngoài mesh.
      * Edge `X` (A→B) và `-X` (B→A) có centerline cách nhau theo phương ngang.
        Snap XY về cùng cạnh polygon kéo cả hai endpoint sát lại nhau → 2 lane mesh
        chồng lên nhau.

    Z snap vẫn cần: với OSM 3D có cao độ thay đổi (cầu vượt, dốc), endpoint lane Z
    của SUMO có thể lệch junction Z ~1m → khe hở dọc trong Unity. Z interpolation
    dọc cạnh polygon gần nhất xóa khe hở mà không động tới vị trí ngang.
    """
    if not polygon or len(polygon) < 2:
        return point
    px, py, pz = point[0], point[1], point[2]
    best_dist_sq = float('inf')
    best_qz = pz
    n = len(polygon)
    for i in range(n):
        ax, ay, az = polygon[i]
        bx, by, bz = polygon[(i + 1) % n]
        dx, dy = bx - ax, by - ay
        len_sq = dx * dx + dy * dy
        if len_sq < 1e-9:
            continue
        t = ((px - ax) * dx + (py - ay) * dy) / len_sq
        if t < 0.0:
            t = 0.0
        elif t > 1.0:
            t = 1.0
        qx = ax + t * dx
        qy = ay + t * dy
        d_sq = (qx - px) ** 2 + (qy - py) ** 2
        if d_sq < best_dist_sq:
            best_dist_sq = d_sq
            best_qz = az + t * (bz - az)
    if best_dist_sq > max_dist * max_dist:
        return point
    return (px, py, best_qz)


class EdgeReader:
    NET_XML_PATH = os.path.join(os.path.dirname(__file__), '../SUMO_xml/HelloWorld.net.xml')

    @staticmethod
    def parse_shape(shape):
        """Parse SUMO `shape` attribute (chuỗi `x1,y1[,z1] x2,y2[,z2] ...`) thành list of {x,y,z} dict."""
        points = []
        for token in shape.strip().split(' '):
            parts = token.split(',')
            if len(parts) < 2:
                continue
            x = round(float(parts[0]), 3)
            y = round(float(parts[1]), 3)
            z = round(float(parts[2]), 3) if len(parts) >= 3 else 0.0
            points.append({"x": x, "y": y, "z": z})
        return points

    @staticmethod
    def classify_lane(lane):
        """Trả về 'pedestrian' nếu lane chỉ cho người đi bộ, ngược lại 'generic'."""
        allow = lane.get('allow', '')
        disallow = lane.get('disallow', '')
        if 'pedestrian' in allow and 'passenger' not in allow:
            return 'pedestrian'
        if 'pedestrian' in disallow:
            return 'generic'
        return 'generic'

    @staticmethod
    def _parse_type_widths(root):
        """Đọc {type_id: width} từ các <type> ở đầu .net.xml (vd: highway.footway width=2.0)."""
        widths = {}
        for t in root.findall('type'):
            tid = t.get('id')
            w = t.get('width')
            if not tid or w is None:
                continue
            try:
                widths[tid] = float(w)
            except ValueError:
                continue
        return widths

    @staticmethod
    def lane_width(lane, edge_type, type_widths):
        """Width per lane theo thứ tự: <lane width> → <type width> cho edge_type → SUMO default.

        Đây là điểm chốt sửa lỗi "lane render hẹp" — không gán fallback dựa trên classify_lane
        (vốn nhầm `allow="pedestrian delivery bicycle"` thành sidewalk 2m); thay vào đó tra
        bảng width của highway type mà SUMO đã emit (`<type ... width="..."/>`).
        """
        w = lane.get('width')
        if w is not None:
            try:
                return round(float(w), 3)
            except ValueError:
                pass
        if edge_type:
            t_w = type_widths.get(edge_type)
            if t_w is not None:
                return round(t_w, 3)
        return SUMO_DEFAULT_LANE_WIDTH

    @staticmethod
    def _snap_endpoint(pt_dict, polygon):
        """Snap CHỈ Z của dict {x,y,z} theo polygon junction, giữ nguyên X/Y."""
        if polygon is None:
            return pt_dict
        x, y, z = _snap_z_to_polygon((pt_dict["x"], pt_dict["y"], pt_dict["z"]), polygon)
        return {"x": round(x, 3), "y": round(y, 3), "z": round(z, 3)}

    @classmethod
    def read_edges(cls):
        edges = []
        if not os.path.exists(cls.NET_XML_PATH):
            print(f"Error: {cls.NET_XML_PATH} does not exist.")
            return edges

        tree = ET.parse(cls.NET_XML_PATH)
        root = tree.getroot()
        polygons = CrossRoadReader.get_junction_polygons()
        type_widths = cls._parse_type_widths(root)

        snapped_count = 0
        for edge in root.findall('edge'):
            if 'function' in edge.attrib:
                continue

            edge_id = edge.get('id')
            edge_type = edge.get('type', '')
            from_id = edge.get('from')
            to_id = edge.get('to')
            from_poly = polygons.get(from_id) if from_id else None
            to_poly = polygons.get(to_id) if to_id else None

            lanes_out = []

            for lane in edge.findall('lane'):
                shape = lane.get('shape')
                if not shape:
                    continue

                points = cls.parse_shape(shape)
                if not points:
                    continue

                # Snap CHỈ Z (cao độ) của 2 endpoint theo polygon junction để khớp độ cao
                # — không snap XY vì sẽ kéo sidewalk vào trong junction và chồng các lane
                # ngược chiều lên nhau. Xem docstring _snap_z_to_polygon.
                if from_poly is not None and len(points) >= 1:
                    before = points[0]
                    points[0] = cls._snap_endpoint(before, from_poly)
                    if points[0] != before:
                        snapped_count += 1
                if to_poly is not None and len(points) >= 1:
                    before = points[-1]
                    points[-1] = cls._snap_endpoint(before, to_poly)
                    if points[-1] != before:
                        snapped_count += 1

                lanes_out.append({
                    "t": cls.classify_lane(lane),
                    "p": points,
                    "w": cls.lane_width(lane, edge_type, type_widths),
                })

            if not lanes_out:
                continue

            # Edge position = điểm ĐẦU của lane đầu tiên (làn ngoài cùng). Khớp Edge.cs đặt
            # transform.position = origin tại điểm đầu, mesh vertex tính relative tới origin.
            base_points = lanes_out[0]["p"]
            head = base_points[0]
            position = {"x": head["x"], "y": head["y"], "z": head["z"]}

            edges.append({
                "i": edge_id,
                "p": position,
                "ls": lanes_out,
            })

        if not edges:
            print("No edges found in the file.")
        else:
            print(f"[EdgeReader] Snapped {snapped_count} lane endpoints to junction polygons.")

        return edges


# Kiểm tra hoạt động của class
if __name__ == "__main__":
    EdgeReader.read_edges()
