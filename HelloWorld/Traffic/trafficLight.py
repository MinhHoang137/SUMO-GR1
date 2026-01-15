import json
import math
import socket

MAX_PACKET_SIZE = 4096



def _shape_point_to_xyz(point):
    """Convert a traci lane shape point to (x, y, z).

    traci.lane.getShape() commonly returns (x, y) points, but 3D networks may provide
    (x, y, z). If z is missing, default to 0.
    """
    if point is None:
        return 0.0, 0.0, 0.0
    x = float(point[0]) if len(point) >= 1 else 0.0
    y = float(point[1]) if len(point) >= 2 else 0.0
    z = float(point[2]) if len(point) >= 3 else 0.0
    return x, y, z

class TrafficLightData:
    def __init__(self, id, position, state, direction):
        self.id = id
        self.type = "traffic_light"
        self.position = position
        self.state = state
        self.direction = direction

    def to_dict(self):
        return {
            "id": self.id,
            "type": self.type,
            "position": self.position,    # Sử dụng mảng [x, y, z]
            "direction": self.direction,  # Sử dụng mảng [x, y, z]
            "state": self.state
        }

def read_traffic_lights(traci):
    """Đọc dữ liệu đèn giao thông từ SUMO và trả về danh sách dict"""
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

                start_x, start_y, start_z = _shape_point_to_xyz(start)
                end_x, end_y, end_z = _shape_point_to_xyz(end)

                # Output raw SUMO coordinates: (x, y, z)
                position = {"x": end_x, "y": end_y, "z": end_z}
                direction = {"x": end_x - start_x, "y": end_y - start_y, "z": end_z - start_z}

                signal = state[i] if i < len(state) else 'r'
                traffic_state = {'r': 0, 'y': 1, 'g': 2, 'G': 2}.get(signal, 0)

                traffic_light = TrafficLightData(
                    id=lane_id,
                    position=position,
                    direction=direction,
                    state=traffic_state
                )
                traffic_lights.append(traffic_light.to_dict())

    return traffic_lights






# ==============================
# Gọi từ file ngoài như sau:
# from traffic_light import read_and_send_traffic_lights
# import traci
#
# traci.start([...])  # Khởi động SUMO
# read_and_send_traffic_lights(traci)
