
import os
import json
import socket
import xml.etree.ElementTree as ET
import math
import time

class CrossingReader:
    NET_XML_PATH = os.path.join(os.path.dirname(__file__), 'HelloWorld.net.xml')
    HOST = '127.0.0.1'
    PORT = 5051
    CHUNK_SIZE = 4096
    TIMEOUT = 5  # seconds
    MAX_RETRIES = 5

    @classmethod
    def parse_shape(cls, shape):
        points = shape.strip().split(' ')
        vertices = [(float(p.split(',')[0]), float(p.split(',')[1])) for p in points]
        return vertices

    @classmethod
    def read_crossings(cls):
        if not os.path.exists(cls.NET_XML_PATH):
            print(f"Error: {cls.NET_XML_PATH} does not exist.")
            return

        tree = ET.parse(cls.NET_XML_PATH)
        root = tree.getroot()

        crossings = []
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

                            direction = {"x": dx / magnitude, "y": dy / magnitude} if magnitude != 0 else {"x": 0, "y": 0}

                            crossing_data = {
                                "id": crossing_id,
                                "start": {"x": start[0], "y": start[1]},
                                "end": {"x": end[0], "y": end[1]},
                                "width": width,
                                "length": length,
                                "direction": direction
                            }
                            crossings.append(crossing_data)

        if crossings:
            cls.send_crossings(crossings)
        else:
            print("No crossings found in the file.")

    @classmethod
    def send_crossings(cls, crossings):
        data = json.dumps(crossings, ensure_ascii=False) + "__EOF__"
        encoded = data.encode('utf-8')

        retries = 0
        while retries < cls.MAX_RETRIES:
            try:
                with socket.create_connection((cls.HOST, cls.PORT), timeout=cls.TIMEOUT) as sock:
                    print(f"Connected to Unity on port {cls.PORT}")
                    for i in range(0, len(encoded), cls.CHUNK_SIZE):
                        chunk = encoded[i:i+cls.CHUNK_SIZE]
                        sock.sendall(chunk)
                    print("Crossing data sent successfully.")
                    break
            except (socket.timeout, ConnectionRefusedError) as e:
                retries += 1
                print(f"Connection failed (attempt {retries}/{cls.MAX_RETRIES}): {e}")
                time.sleep(1)
        else:
            print("Failed to send crossing data after multiple retries.")

if __name__ == "__main__":
    CrossingReader.read_crossings()

