
import os
import xml.etree.ElementTree as ET

from Traffic.crossRoad import CrossRoadReader


# Default lane widths (in meters) khi <lane> không khai báo width.
DEFAULT_ROAD_LANE_WIDTH = 3.2
DEFAULT_WALKING_LANE_WIDTH = 2.0

# Khoảng cách XY tối đa để chấp nhận snap. Lane endpoint xa hơn ngưỡng này → không snap
# (data bất thường, tránh kéo lane sai vị trí).
SNAP_MAX_DIST = 5.0


def _snap_to_polygon(point, polygon, max_dist=SNAP_MAX_DIST):
    """Project (x, y, z) point lên biên polygon trong mặt XY, nội suy Z dọc đoạn gần nhất.

    polygon: list[(x, y, z)] đỉnh đi vòng biên. Coi như đóng (segment cuối nối về đỉnh đầu).
    Trả về (x, y, z) mới nếu khoảng cách projection ≤ max_dist, ngược lại trả nguyên point.
    """
    if not polygon or len(polygon) < 2:
        return point
    px, py, _pz = point[0], point[1], point[2]
    best_dist_sq = float('inf')
    best = point
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
        qz = az + t * (bz - az)
        d_sq = (qx - px) ** 2 + (qy - py) ** 2
        if d_sq < best_dist_sq:
            best_dist_sq = d_sq
            best = (qx, qy, qz)
    if best_dist_sq > max_dist * max_dist:
        return point
    return best


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
    def lane_width(lane, lane_type):
        w = lane.get('width')
        if w is not None:
            try:
                return round(float(w), 3)
            except ValueError:
                pass
        return DEFAULT_WALKING_LANE_WIDTH if lane_type == 'pedestrian' else DEFAULT_ROAD_LANE_WIDTH

    @staticmethod
    def _snap_endpoint(pt_dict, polygon):
        """Snap dict {x,y,z} vào polygon, trả về dict mới (đã round 3 số)."""
        if polygon is None:
            return pt_dict
        x, y, z = _snap_to_polygon((pt_dict["x"], pt_dict["y"], pt_dict["z"]), polygon)
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

        snapped_count = 0
        for edge in root.findall('edge'):
            if 'function' in edge.attrib:
                continue

            edge_id = edge.get('id')
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

                # Snap endpoint XYZ vào polygon junction tương ứng. SUMO emit lane shape lệch
                # khỏi biên junction cả XY (~1m) lẫn Z (~1m) → mesh Unity hở/lệch độ cao.
                # Project lên đoạn polygon gần nhất + nội suy Z xoá triệt để khe hở.
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

                lane_type = cls.classify_lane(lane)
                lanes_out.append({
                    "t": lane_type,
                    "p": points,
                    "w": cls.lane_width(lane, lane_type),
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
