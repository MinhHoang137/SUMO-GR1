
import os
import xml.etree.ElementTree as ET
import math

class CrossingReader:
    NET_XML_PATH = os.path.join(os.path.dirname(__file__), '../SUMO_xml/HelloWorld.net.xml')
    DEFAULT_Z = 0.0

    @classmethod
    def _to_coord(cls, x: float, y: float, z: float = 0.0):
        return {"x": float(x), "y": float(y), "z": float(z)}

    @classmethod
    def parse_shape(cls, shape: str, default_z: float | None = None):
        """Parse SUMO lane shape.

        Supports points in form "x,y" or "x,y,z".
        If z is missing, defaults to `default_z` (or 0.0).
        Returns list of Coordinate dicts: {x,y,z}.
        """
        if default_z is None:
            default_z = cls.DEFAULT_Z

        points = shape.strip().split()
        vertices = []
        for point in points:
            parts = point.split(',')
            if len(parts) < 2:
                continue
            x = float(parts[0])
            y = float(parts[1])
            z = float(parts[2]) if len(parts) >= 3 and parts[2] != '' else float(default_z)
            vertices.append(cls._to_coord(x, y, z))
        return vertices

    @classmethod
    def read_crossings(cls, net_xml_path: str | None = None):
        crossings = []
        net_path = net_xml_path or cls.NET_XML_PATH
        if not os.path.exists(net_path):
            print(f"Error: {net_path} does not exist.")
            return crossings

        tree = ET.parse(net_path)
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

                            dx = end["x"] - start["x"]
                            dy = end["y"] - start["y"]
                            dz = end["z"] - start["z"]
                            magnitude = math.sqrt(dx**2 + dy**2 + dz**2)

                            direction = (
                                {"x": dx / magnitude, "y": dy / magnitude, "z": dz / magnitude}
                                if magnitude != 0
                                else {"x": 0.0, "y": 0.0, "z": 0.0}
                            )

                            crossing_data = {
                                "id": crossing_id,
                                "start": start,
                                "end": end,
                                "width": width,
                                "length": length,
                                "direction": direction
                            }
                            crossings.append(crossing_data)

        if not crossings:
            print("No crossings found in the file.")

        return  crossings

if __name__ == "__main__":
    CrossingReader.read_crossings()

