

import os
import json
import socket
import xml.etree.ElementTree as ET
from math import atan2
import time

class CrossRoadReader:
    NET_XML_PATH = os.path.join(os.path.dirname(__file__), 'HelloWorld.net.xml')
    HOST = '127.0.0.1'
    PORT = 5050
    TIMEOUT = 5
    MAX_RETRIES = 3
    BUFFER_SIZE = 4096
    END_TAG = b'__EOF__'  # Nhãn kết thúc chuỗi

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

    @classmethod
    def send_crossroads(cls, crossroads):
        data = json.dumps(crossroads, ensure_ascii=False).encode('utf-8')
        total_sent = 0

        for attempt in range(cls.MAX_RETRIES):
            try:
                with socket.create_connection((cls.HOST, cls.PORT), timeout=cls.TIMEOUT) as sock:
                    print(f"Connected to {cls.HOST}:{cls.PORT}")

                    while total_sent < len(data):
                        end = min(total_sent + cls.BUFFER_SIZE, len(data))
                        sent = sock.send(data[total_sent:end])
                        if sent == 0:
                            raise RuntimeError("Socket connection broken")
                        total_sent += sent

                    # Gửi nhãn EOF để đánh dấu kết thúc dữ liệu
                    sock.sendall(cls.END_TAG)
                    print("Data sent successfully with EOF marker.")
                    return
            except socket.timeout:
                print(f"Attempt {attempt + 1}: Timeout occurred. Retrying...")
                time.sleep(1)
            except Exception as e:
                print(f"Attempt {attempt + 1}: Error occurred - {e}")
                time.sleep(1)

        print("Failed to send data after multiple attempts.")

if __name__ == "__main__":
    CrossRoadReader.read_all_junctions()
