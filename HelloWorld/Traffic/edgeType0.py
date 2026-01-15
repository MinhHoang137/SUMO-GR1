
import os
import xml.etree.ElementTree as ET


class EdgeReader:
    NET_XML_PATH = os.path.join(os.path.dirname(__file__), '../SUMO_xml/HelloWorld.net.xml')
    DEFAULT_LANE_WIDTH = 3.2

    @staticmethod
    def _to_coord(x: float, y: float, z: float = 0.0):
        return {"x": float(x), "y": float(y), "z": float(z)}

    @classmethod
    def parse_shape(cls, shape: str):
        """Parse SUMO lane shape into a list of Coordinate dicts compatible with Unity."""
        points = shape.strip().split()
        coords = []
        for point in points:
            parts = point.split(',')
            if len(parts) < 2:
                continue

            x_str = parts[0]
            y_str = parts[1]
            # Some SUMO networks include elevation: "x,y,z". If absent, default z=0.
            z_str = parts[2] if len(parts) >= 3 and parts[2] != '' else '0'
            coords.append(cls._to_coord(float(x_str), float(y_str), float(z_str)))
        return coords

    @staticmethod
    def _lane_type_from_attrib(lane_attrib: dict) -> str:
        allow = (lane_attrib.get('allow') or '').strip()
        disallow = (lane_attrib.get('disallow') or '').strip()

        # Common SUMO convention: pedestrian lanes have allow containing 'pedestrian'.
        if allow:
            tokens = allow.split()
            if 'pedestrian' in tokens:
                return 'pedestrian'
            # If SUMO specifies a single class, use it (bus, bicycle, etc.).
            return tokens[0]

        # If pedestrians are explicitly disallowed, treat as generic road lane.
        if disallow and 'pedestrian' in disallow.split():
            return 'generic'

        return 'generic'

    @staticmethod
    def _compute_edge_position(lanes: list) -> dict:
        """Compute an approximate centroid for the edge from all lane points."""
        sum_x = 0.0
        sum_y = 0.0
        sum_z = 0.0
        count = 0
        for lane in lanes:
            for p in lane.get('points', []):
                sum_x += float(p.get('x', 0.0))
                sum_y += float(p.get('y', 0.0))
                sum_z += float(p.get('z', 0.0))
                count += 1

        if count == 0:
            return {"x": 0.0, "y": 0.0, "z": 0.0}
        return {"x": sum_x / count, "y": sum_y / count, "z": sum_z / count}

    @classmethod
    def read_edges(cls, net_xml_path: str | None = None):
        edges = []
        net_path = net_xml_path or cls.NET_XML_PATH
        if not os.path.exists(net_path):
            print(f"Error: {net_path} does not exist.")
            return edges

        tree = ET.parse(net_path)
        root = tree.getroot()

        for edge in root.findall('edge'):
            if 'function' in edge.attrib:
                continue

            edge_id = edge.get('id')
            lanes_by_index = {}
            for lane in edge.findall('lane'):
                shape = lane.get('shape')
                if not shape:
                    continue

                try:
                    index = int(lane.get('index'))
                except (TypeError, ValueError):
                    # Fallback: keep stable ordering even if index missing/invalid
                    index = len(lanes_by_index)

                lane_data = {
                    "type": cls._lane_type_from_attrib(lane.attrib),
                    "points": cls.parse_shape(shape),
                    "width": float(lane.get('width') or cls.DEFAULT_LANE_WIDTH),
                }
                lanes_by_index[index] = lane_data

            lanes = [lanes_by_index[i] for i in sorted(lanes_by_index.keys())]
            edge_data = {
                "id": edge_id,
                "lanes": lanes,
                "position": cls._compute_edge_position(lanes),
            }
            edges.append(edge_data)

        if not edges:
            print("No edges found in the file.")

        return edges


# Kiểm tra hoạt động của class
if __name__ == "__main__":
    EdgeReader.read_edges()
