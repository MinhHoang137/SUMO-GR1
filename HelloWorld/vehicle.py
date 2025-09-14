import json
import math
import socket
from typing import Any

MAX_PACKET_SIZE = 4096  # 4KB để tránh lỗi tràn bộ đệm

class VehicleData:
    def __init__(self, id, position, forward, speed, lane,
                 turn_left, turn_right, is_braking):
        self.id = id
        self.type = "vehicle"
        self.position = position
        self.forward = forward
        self.speed = speed
        self.lane = lane
        self.turnLeft = turn_left
        self.turnRight = turn_right
        self.isBraking = is_braking

    def to_dict(self):
        return {
            "id": self.id,
            "type": self.type,
            "position": self.position,
            "forward": self.forward,
            "speed": self.speed,
            "lane": self.lane,
            "turnLeft": self.turnLeft,
            "turnRight": self.turnRight,
            "isBraking": self.isBraking
        }

def read_vehicles(traci):
    vehicles = []
    try:
        vehicle_ids = traci.vehicle.getIDList()

        for vehicle_id in vehicle_ids:
            try:
                # Lấy dữ liệu từ SUMO
                position = traci.vehicle.getPosition(vehicle_id)  # Lấy vị trí [x, y]
                speed = traci.vehicle.getSpeed(vehicle_id)        # Lấy tốc độ
                lane = traci.vehicle.getLaneID(vehicle_id)        # Lấy làn đường

                # Lấy trạng thái đèn báo rẽ và phanh
                signals = traci.vehicle.getSignals(vehicle_id)
                turn_left = (signals & 0x02) != 0
                turn_right = (signals & 0x01) != 0
                is_braking = (signals & 0x04) != 0

                # Lấy hướng của xe (theo đơn vị góc độ)
                angle = traci.vehicle.getAngle(vehicle_id)

                # Chuyển hướng từ góc độ thành vector đơn vị [x, y]
                radian = math.radians(angle)
                forward = [math.cos(radian), math.sin(radian)]

                vehicle = VehicleData(
                    vehicle_id,
                    position,  # Giữ nguyên vị trí [x, y] của SUMO
                    forward,   # Giữ nguyên hướng [x, y] dưới dạng vector đơn vị
                    speed,
                    lane,
                    turn_left,
                    turn_right,
                    is_braking
                )
                vehicles.append(vehicle.to_dict())

            except Exception as e:
                print(f"Error reading vehicle data for {vehicle_id}: {e}")

        if not vehicles:
            print("No vehicle data to send.")

    except:
        print("Error reading vehicles from SUMO.")

    return vehicles


def read_and_send_vehicles(traci, host='127.0.0.1', port=5051):
    try:
        vehicles = []
        vehicle_ids = traci.vehicle.getIDList()

        for vehicle_id in vehicle_ids:
            try:
                # Lấy dữ liệu từ SUMO
                position = traci.vehicle.getPosition(vehicle_id)  # Lấy vị trí [x, y]
                speed = traci.vehicle.getSpeed(vehicle_id)        # Lấy tốc độ
                lane = traci.vehicle.getLaneID(vehicle_id)        # Lấy làn đường

                # Lấy trạng thái đèn báo rẽ và phanh
                signals = traci.vehicle.getSignals(vehicle_id)
                turn_left = (signals & 0x02) != 0
                turn_right = (signals & 0x01) != 0
                is_braking = (signals & 0x04) != 0

                # Lấy hướng của xe (theo đơn vị góc độ)
                angle = traci.vehicle.getAngle(vehicle_id)

                # Chuyển hướng từ góc độ thành vector đơn vị [x, y]
                radian = math.radians(angle)
                forward = [math.cos(radian), math.sin(radian)]

                vehicle = VehicleData(
                    vehicle_id,
                    position,  # Giữ nguyên vị trí [x, y] của SUMO
                    forward,   # Giữ nguyên hướng [x, y] dưới dạng vector đơn vị
                    speed,
                    lane,
                    turn_left,
                    turn_right,
                    is_braking
                )
                vehicles.append(vehicle.to_dict())

            except Exception as e:
                print(f"Error reading vehicle data for {vehicle_id}: {e}")

        if not vehicles:
            print("No vehicle data to send.")
            return

        # Kết nối socket và gửi dữ liệu
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(5)  # Timeout 5 giây để tránh treo
            s.connect((host, port))

            # Chuyển danh sách dữ liệu thành JSON
            data = json.dumps(vehicles)
            total_size = len(data)
            num_packets = math.ceil(total_size / MAX_PACKET_SIZE)

            print(f"Sending {num_packets} packets of vehicle data...")

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
            # print("All vehicle data sent successfully!")

            # Nhận phản hồi từ Unity (nếu có)
            try:
                response = s.recv(4096)
                if response:
                    print(f"Response from Unity: {response.decode('utf-8')}")
            except socket.timeout:
                print("No response from Unity (timeout).")

    except Exception as e:
        print(f"Error sending vehicle data: {e}")



# ==============================
# Gọi từ file ngoài như sau:
# from vehicle import read_and_send_vehicles
# import traci
#
# traci.start([...])  # Khởi động SUMO
# read_and_send_vehicles(traci)
