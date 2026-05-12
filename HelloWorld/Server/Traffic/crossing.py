
import os
import xml.etree.ElementTree as ET
import math

class CrossingReader:
    NET_XML_PATH = os.path.join(os.path.dirname(__file__), '../SUMO_xml/HelloWorld.net.xml')

    @classmethod
    def parse_shape(cls, shape):
        points = shape.strip().split(' ')
        vertices = [(float(p.split(',')[0]), float(p.split(',')[1])) for p in points]
        return vertices

    @classmethod
    def read_crossings(cls):
        crossings = []
        if not os.path.exists(cls.NET_XML_PATH):
            print(f"Error: {cls.NET_XML_PATH} does not exist.")
            return crossings

        tree = ET.parse(cls.NET_XML_PATH)
        root = tree.getroot()


        for edge in root.findall('edge'):
            if edge.get('function') == 'crossing':
                for lane in edge.findall('lane'):
                    crossing_id = lane.get('id')
                    shape = lane.get('shape')
                    width = float(lane.get('width', 0))
                    length = float(lane.get('length', 0))

                    if shape:
                        vertices = cls.parse_shape(shape)
                        if len(vertices) >= 2:
                            start = vertices[0]
                            end = vertices[-1]

                            dx = end[0] - start[0]
                            dy = end[1] - start[1]
                            magnitude = math.sqrt(dx**2 + dy**2)

                            direction = {"x": round(dx / magnitude, 3), "y": round(dy / magnitude, 3)} if magnitude != 0 else {"x": 0, "y": 0}

                            crossing_data = {
                                "i": crossing_id,
                                "st": {"x": round(start[0], 3), "y": round(start[1], 3)},
                                "ed": {"x": round(end[0], 3), "y": round(end[1], 3)},
                                "w": round(width, 3),
                                "l": round(length, 3),
                                "d": direction
                            }
                            crossings.append(crossing_data)

        if not crossings:
            print("No crossings found in the file.")

        return  crossings

if __name__ == "__main__":
    CrossingReader.read_crossings()

