

import os
import xml.etree.ElementTree as ET
from math import atan2

class CrossRoadReader:
    NET_XML_PATH  = os.path.join(os.path.dirname(__file__), '../SUMO_xml/HelloWorld.net.xml')

    @classmethod
    def parse_shape(cls, shape: str, default_z: float = 0.0):
        """Parse SUMO junction shape.

        Supports points in form "x,y" or "x,y,z".
        If z is missing, defaults to `default_z` (typically junction z or 0).
        Returns list of (x, y, z) tuples.
        """
        points = shape.strip().split()
        vertices = []
        for point in points:
            parts = point.split(',')
            if len(parts) < 2:
                continue
            x = float(parts[0])
            y = float(parts[1])
            z = float(parts[2]) if len(parts) >= 3 and parts[2] != '' else float(default_z)
            vertices.append((x, y, z))
        return vertices

    @classmethod
    def sort_clockwise(cls, vertices):
        if not vertices:
            return []
        center_x = sum(v[0] for v in vertices) / len(vertices)
        center_y = sum(v[1] for v in vertices) / len(vertices)
        # sort on x/y plane; keep z attached to each vertex
        return sorted(vertices, key=lambda v: atan2(v[1] - center_y, v[0] - center_x), reverse=True)

    @classmethod
    def read_all_junctions(cls, net_xml_path: str | None = None):
        net_path = net_xml_path or cls.NET_XML_PATH
        if not os.path.exists(net_path):
            print(f"Error: {net_path} does not exist.")
            return []

        tree = ET.parse(net_path)
        root = tree.getroot()

        crossroads = []

        for junction in root.findall('junction'):
            junction_id = junction.get('id')
            # junction_type = junction.get('type', 'unknown')
            x = float(junction.get('x'))
            y = float(junction.get('y'))
            z = float(junction.get('z') or 0.0)
            shape = junction.get('shape')

            if shape:
                vertices = cls.parse_shape(shape, default_z=z)
                sorted_vertices = cls.sort_clockwise(vertices)
                crossroad = {
                    "id": junction_id,
                    "position": {"x": x, "y": y, "z": z},
                    "vertices": [{"x": v[0], "y": v[1], "z": v[2]} for v in sorted_vertices]
                }
                crossroads.append(crossroad)

        if not crossroads:
            print("No junctions found in the file.")

        return crossroads

if __name__ == "__main__":
    CrossRoadReader.read_all_junctions()
