import json
import math
import socket
from typing import Any

MAX_PACKET_SIZE = 4096  # 4KB để tránh lỗi tràn bộ đệm


def _get_vehicle_position_xyz(traci, vehicle_id: str) -> list[float]:
    """Return raw SUMO position as [x, y, z].

    Prefers TraCI 3D position when available; otherwise defaults z=0.
    """
    getter3d = getattr(getattr(traci, 'vehicle', None), 'getPosition3D', None)
    if callable(getter3d):
        try:
            x, y, z = getter3d(vehicle_id)
            return [float(x), float(y), float(z)]
        except Exception:
            pass

    x, y = traci.vehicle.getPosition(vehicle_id)
    return [float(x), float(y), 0.0]

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
                position = _get_vehicle_position_xyz(traci, vehicle_id)  # [x, y, z]
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
                forward = [math.cos(radian), math.sin(radian), 0.0]

                vehicle = VehicleData(
                    vehicle_id,
                    position,  # Giữ nguyên vị trí [x, y] của SUMO
                    forward,   # Hướng [x, y, z] (z mặc định 0)
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





# ==============================
# Gọi từ file ngoài như sau:
# from vehicle import read_and_send_vehicles
# import traci
#
# traci.start([...])  # Khởi động SUMO
# read_and_send_vehicles(traci)
