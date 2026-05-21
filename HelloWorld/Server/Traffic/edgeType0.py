
import os
import xml.etree.ElementTree as ET


# Default lane widths (in meters) khi <lane> không khai báo width.
DEFAULT_ROAD_LANE_WIDTH = 3.2
DEFAULT_WALKING_LANE_WIDTH = 2.0


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

    @classmethod
    def read_edges(cls):
        edges = []
        if not os.path.exists(cls.NET_XML_PATH):
            print(f"Error: {cls.NET_XML_PATH} does not exist.")
            return edges

        tree = ET.parse(cls.NET_XML_PATH)
        root = tree.getroot()

        for edge in root.findall('edge'):
            if 'function' in edge.attrib:
                continue

            edge_id = edge.get('id')
            lanes_out = []

            for lane in edge.findall('lane'):
                shape = lane.get('shape')
                if not shape:
                    continue

                points = cls.parse_shape(shape)
                if not points:
                    continue

                lane_type = cls.classify_lane(lane)
                lanes_out.append({
                    "t": lane_type,
                    "p": points,
                    "w": cls.lane_width(lane, lane_type),
                })

            if not lanes_out:
                continue

            # Center position: trung điểm của lane đầu tiên (làn ngoài cùng), khớp Edge.cs lấy lanes[0] làm base.
            base_points = lanes_out[0]["p"]
            mid = base_points[len(base_points) // 2]
            position = {"x": mid["x"], "y": mid["y"], "z": mid["z"]}

            edges.append({
                "i": edge_id,
                "p": position,
                "ls": lanes_out,
            })

        if not edges:
            print("No edges found in the file.")

        return edges


# Kiểm tra hoạt động của class
if __name__ == "__main__":
    EdgeReader.read_edges()
