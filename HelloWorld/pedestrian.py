import json
import math
import socket

MAX_PACKET_SIZE = 4096  # 4KB để tránh lỗi tràn bộ đệm

class PedestrianData:
    def __init__(self, id, position, forward, speed, lane):
        self.id = id
        self.type = "pedestrian"
        self.position = position
        self.forward = forward
        self.speed = speed
        self.lane = lane

    def to_dict(self):
        return {
            "id": self.id,
            "type": self.type,
            "position": self.position,
            "forward": self.forward,
            "speed": self.speed,
            "lane": self.lane
        }

def read_and_send_pedestrians(traci, host='127.0.0.1', port=5052):
    try:
        pedestrians = []
        pedestrian_ids = traci.person.getIDList()

        for pedestrian_id in pedestrian_ids:
            try:
                # Lấy dữ liệu từ SUMO
                position = traci.person.getPosition(pedestrian_id)  # Lấy vị trí [x, y]
                speed = traci.person.getSpeed(pedestrian_id)        # Lấy tốc độ
                lane = traci.person.getLaneID(pedestrian_id)        # Lấy làn đường

                # Lấy hướng của pedestrian (theo đơn vị góc độ)
                angle = traci.person.getAngle(pedestrian_id)

                # Chuyển hướng từ góc độ thành vector đơn vị [x, y]
                radian = math.radians(angle)
                forward = [math.cos(radian), math.sin(radian)]

                pedestrian = PedestrianData(
                    pedestrian_id,
                    position,  # Giữ nguyên vị trí [x, y] của SUMO
                    forward,   # Giữ nguyên hướng [x, y] dưới dạng vector đơn vị
                    speed,
                    lane
                )
                pedestrians.append(pedestrian.to_dict())

            except Exception as e:
                print(f"Error reading pedestrian data for {pedestrian_id}: {e}")

        if not pedestrians:
            print("No pedestrian data to send.")
            return

        # Kết nối socket và gửi dữ liệu
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(5)  # Timeout 5 giây để tránh treo
            s.connect((host, port))

            # Chuyển danh sách dữ liệu thành JSON
            data = json.dumps(pedestrians)
            total_size = len(data)
            num_packets = math.ceil(total_size / MAX_PACKET_SIZE)

            print(f"Sending {num_packets} packets of pedestrian data...")

            # Gửi từng gói nhỏ
            for i in range(num_packets):
                start = i * MAX_PACKET_SIZE
                end = min(start + MAX_PACKET_SIZE, total_size)
                packet = data[start:end]

                try:
                    s.sendall(packet.encode('utf-8'))
                except socket.error as e:
                    print(f"Error sending packet {i + 1}/{num_packets}: {e}")
                    return

            # Gửi thông báo kết thúc
            s.sendall(b"<END>")
            # print("All pedestrian data sent successfully!")

            # Nhận phản hồi từ Unity (nếu có)
            try:
                response = s.recv(1024)
                if response:
                    print(f"Response from Unity: {response.decode('utf-8')}")
            except socket.timeout:
                print("No response from Unity (timeout).")

    except Exception as e:
        print(f"Error sending pedestrian data: {e}")
