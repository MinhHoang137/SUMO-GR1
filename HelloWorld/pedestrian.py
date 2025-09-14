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

def read_pedestrians(traci):
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

    return pedestrians

