import json
import math
import socket

MAX_PACKET_SIZE = 4096  # 4KB để tránh lỗi tràn bộ đệm


def _get_pedestrian_position_xyz(traci, pedestrian_id: str) -> list[float]:
    """Return raw SUMO person position as [x, y, z].

    Prefers TraCI 3D position when available; otherwise defaults z=0.
    """
    getter3d = getattr(getattr(traci, 'person', None), 'getPosition3D', None)
    if callable(getter3d):
        try:
            x, y, z = getter3d(pedestrian_id)
            return [float(x), float(y), float(z)]
        except Exception:
            pass

    x, y = traci.person.getPosition(pedestrian_id)
    return [float(x), float(y), 0.0]

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
            position = _get_pedestrian_position_xyz(traci, pedestrian_id)  # [x, y, z]
            speed = traci.person.getSpeed(pedestrian_id)        # Lấy tốc độ
            lane = traci.person.getLaneID(pedestrian_id)        # Lấy làn đường

            # Lấy hướng của pedestrian (theo đơn vị góc độ)
            angle = traci.person.getAngle(pedestrian_id)

            # Chuyển hướng từ góc độ thành vector đơn vị [x, y]
            radian = math.radians(angle)
            forward = [math.cos(radian), math.sin(radian), 0.0]

            pedestrian = PedestrianData(
                pedestrian_id,
                position,  # Giữ nguyên vị trí [x, y] của SUMO
                forward,   # Hướng [x, y, z] (z mặc định 0)
                speed,
                lane
            )
            pedestrians.append(pedestrian.to_dict())

        except Exception as e:
            print(f"Error reading pedestrian data for {pedestrian_id}: {e}")

    return pedestrians

