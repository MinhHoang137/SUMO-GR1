
import os
import json
import xml.etree.ElementTree as ET
import socket


class EdgeReader:
    NET_XML_PATH = os.path.join(os.path.dirname(__file__), 'HelloWorld.net.xml')
    SERVER_HOST = '127.0.0.1'  # Địa chỉ localhost
    SERVER_PORT = 5052  # Cổng 5052
    CHUNK_SIZE = 4096  # Kích thước gói gửi mỗi lần (4096 byte)

    @staticmethod
    def parse_shape(shape):
        points = shape.strip().split(' ')
        vertices = [(float(p.split(',')[0]), float(p.split(',')[1])) for p in points]
        return vertices

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
            road_lanes = {}
            walking_lanes = {}

            for lane in edge.findall('lane'):
                shape = lane.get('shape')
                if not shape:
                    continue

                index = int(lane.get('index'))
                vertices = cls.parse_shape(shape)

                if 'allow' in lane.attrib and 'pedestrian' in lane.get('allow'):
                    walking_lanes[index] = vertices
                elif 'disallow' in lane.attrib and 'pedestrian' in lane.get('disallow'):
                    road_lanes[index] = vertices
                else:
                    road_lanes[index] = vertices

            start_road_lane = road_lanes[max(road_lanes.keys())][0] if road_lanes else None
            end_road_lane = road_lanes[max(road_lanes.keys())][-1] if road_lanes else None
            start_walking_lane = walking_lanes[max(walking_lanes.keys())][0] if walking_lanes else None
            end_walking_lane = walking_lanes[max(walking_lanes.keys())][-1] if walking_lanes else None

            if start_road_lane and end_road_lane:
                direction = {
                    "x": end_road_lane[0] - start_road_lane[0],
                    "y": end_road_lane[1] - start_road_lane[1]
                }
                position = {
                    "x": (start_road_lane[0] + end_road_lane[0]) / 2,
                    "y": (start_road_lane[1] + end_road_lane[1]) / 2
                }
            else:
                direction = None
                position = None

            edge_data = {
                "id": edge_id,
                "startRoadLane": {"x": start_road_lane[0], "y": start_road_lane[1]} if start_road_lane else None,
                "endRoadLane": {"x": end_road_lane[0], "y": end_road_lane[1]} if end_road_lane else None,
                "roadNum": len(road_lanes),
                "startWalkingLane": {"x": start_walking_lane[0],
                                     "y": start_walking_lane[1]} if start_walking_lane else None,
                "endWalkingLane": {"x": end_walking_lane[0], "y": end_walking_lane[1]} if end_walking_lane else None,
                "walkingNum": len(walking_lanes),
                "direction": direction,
                "position": position
            }
            edges.append(edge_data)

        if not edges:
            print("No edges found in the file.")

        return edges

    @classmethod
    def send_edges_in_chunks(cls, edges):
        try:
            # Kết nối đến server Unity qua cổng 5052
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((cls.SERVER_HOST, cls.SERVER_PORT))

                # Chuyển đổi dữ liệu edges thành JSON
                json_data = json.dumps(edges, ensure_ascii=False)

                # Chia dữ liệu thành các gói nhỏ 4096 byte
                for i in range(0, len(json_data), cls.CHUNK_SIZE):
                    chunk = json_data[i:i + cls.CHUNK_SIZE]
                    s.sendall(chunk.encode('utf-8'))

                # Gửi dấu kết thúc khi gửi xong tất cả dữ liệu
                s.sendall(b"__EOF__")
        except Exception as e:
            print(f"Error sending data to Unity: {e}")


# Kiểm tra hoạt động của class
if __name__ == "__main__":
    EdgeReader.read_edges()
