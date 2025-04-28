import json
import math
import socket

MAX_PACKET_SIZE = 4096

class TrafficLightData:
    def __init__(self, id, position, state, direction):
        self.id = id
        self.position = position
        self.state = state
        self.direction = direction

    def to_dict(self):
        return {
            "id": self.id,
            "position": self.position,    # Sử dụng mảng [x, y, z]
            "direction": self.direction,  # Sử dụng mảng [x, y, z]
            "state": self.state
        }

def read_and_send_traffic_lights(traci, host='127.0.0.1', port=5050):
    try:
        traffic_lights = []
        traffic_light_ids = traci.trafficlight.getIDList()

        for tl_id in traffic_light_ids:
            state = traci.trafficlight.getRedYellowGreenState(tl_id)
            controlled_lanes = traci.trafficlight.getControlledLanes(tl_id)

            for i, lane_id in enumerate(controlled_lanes):
                lane = traci.lane.getShape(lane_id)
                if lane:
                    start = lane[0]
                    end = lane[-1]

                    position = [end[0], 5, end[1]]
                    direction = [end[0] - start[0], 0, end[1] - start[1]]

                    signal = state[i] if i < len(state) else 'r'
                    traffic_state = {'r': 0, 'y': 1, 'g': 2, 'G': 2}.get(signal, 0)

                    traffic_light = TrafficLightData(
                        id=lane_id,
                        position=position,
                        direction=direction,
                        state=traffic_state
                    )
                    traffic_lights.append(traffic_light.to_dict())

        # Kết nối và gửi dữ liệu
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((host, port))

            # Chuyển dữ liệu sang JSON
            data = json.dumps(traffic_lights)
            total_size = len(data)
            num_packets = math.ceil(total_size / MAX_PACKET_SIZE)

            print(f"Sending {num_packets} packets...")

            # Gửi lần lượt từng gói dữ liệu
            for i in range(num_packets):
                start = i * MAX_PACKET_SIZE
                end = min(start + MAX_PACKET_SIZE, total_size)
                packet = data[start:end]
                s.sendall(packet.encode('utf-8'))

            # Gửi thông báo kết thúc
            s.sendall(b"<END>")

            # print("All data sent successfully!")

            # Nhận phản hồi từ Unity (nếu cần)
            response = s.recv(1024)
            # print(f"Response from Unity: {response.decode('utf-8')}")

    except Exception as e:
        print(f"Error sending traffic light data: {e}")

# ==============================
# Gọi từ file ngoài như sau:
# from traffic_light import read_and_send_traffic_lights
# import traci
#
# traci.start([...])  # Khởi động SUMO
# read_and_send_traffic_lights(traci)
