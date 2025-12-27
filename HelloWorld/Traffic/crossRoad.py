

import os
import xml.etree.ElementTree as ET
from math import atan2

class CrossRoadReader:
    NET_XML_PATH  = os.path.join(os.path.dirname(__file__), '../SUMO_xml/HelloWorld.net.xml')

    @classmethod
    def parse_shape(cls, shape):
        points = shape.strip().split(' ')
        vertices = [(float(p.split(',')[0]), float(p.split(',')[1])) for p in points]
        return vertices

    @classmethod
    def sort_clockwise(cls, vertices):
        if not vertices:
            return []
        center_x = sum(v[0] for v in vertices) / len(vertices)
        center_y = sum(v[1] for v in vertices) / len(vertices)
        return sorted(vertices, key=lambda v: atan2(v[1] - center_y, v[0] - center_x), reverse=True)

    @classmethod
    def read_all_junctions(cls):
        if not os.path.exists(cls.NET_XML_PATH):
            print(f"Error: {cls.NET_XML_PATH} does not exist.")
            return

        tree = ET.parse(cls.NET_XML_PATH)
        root = tree.getroot()

        crossroads = []

        for junction in root.findall('junction'):
            junction_id = junction.get('id')
            # junction_type = junction.get('type', 'unknown')
            x = float(junction.get('x'))
            y = float(junction.get('y'))
            shape = junction.get('shape')

            if shape:
                vertices = cls.parse_shape(shape)
                sorted_vertices = cls.sort_clockwise(vertices)
                crossroad = {
                    "id": junction_id,
                    "position": [x, y],
                    "vertices": [{"x": v[0], "y": v[1]} for v in sorted_vertices]
                }
                crossroads.append(crossroad)

        if not crossroads:
            print("No junctions found in the file.")

        return crossroads

if __name__ == "__main__":
    CrossRoadReader.read_all_junctions()
