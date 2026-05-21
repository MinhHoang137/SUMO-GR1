import json
import math
import socket

MAX_PACKET_SIZE = 4096

# Chiều cao trụ đèn so với mặt đường (SUMO z = trục đứng).
LIGHT_HEIGHT_SUMO = 5.0


class TrafficLightData:
    def __init__(self, id, position, state, direction):
        self.id = id
        self.type = "traffic_light"
        self.position = position  # SUMO convention (x, y, z_up)
        self.state = state
        self.direction = direction  # SUMO convention (dx, dy, dz)

    def to_dict(self):
        return {
            "i": self.id,
            "t": "tl",
            "p": [round(self.position[0], 2), round(self.position[1], 2), round(self.position[2], 2)],
            "d": [round(self.direction[0], 2), round(self.direction[1], 2), round(self.direction[2], 2)],
            "s": self.state
        }

def read_traffic_lights(traci):
    """Đọc dữ liệu đèn giao thông từ SUMO và trả về danh sách dict (theo convention SUMO; phía C# convert bằng Converter)."""
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

                # SUMO (x, y, z_up): đặt đèn ở cuối lane, nâng cao theo trục đứng.
                position = [end[0], end[1], LIGHT_HEIGHT_SUMO]
                # Direction theo SUMO: vector ngang trong mặt phẳng (x, y), z = 0.
                direction = [end[0] - start[0], end[1] - start[1], 0.0]

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
