import math

from Traffic.lane_shapes import get_z_at_lane_pos


class TrafficerData:
    def __init__(self, id, obj_type, speed, position, forward):
        self.id = id
        self.type = obj_type
        self.speed = speed
        self.position = position
        self.forward = forward

    def to_dict(self):
        short_type = "v" if self.type == "vehicle" else "p" if self.type == "pedestrian" else self.type
        pos = [round(self.position[0], 2), round(self.position[1], 2)]
        if len(self.position) >= 3:
            pos.append(round(self.position[2], 2))
        return {
            "i": self.id,
            "t": short_type,
            "sp": round(self.speed, 2),
            "p": pos,
            "f": [round(self.forward[0], 2), round(self.forward[1], 2)]
        }

def read_trafficers(traci):
    trafficers = []

    # Read vehicles (dùng getPosition3D để có cao độ — cần cho cầu/đèo trong .osm)
    try:
        vehicle_ids = traci.vehicle.getIDList()
        for v_id in vehicle_ids:
            try:
                try:
                    position = traci.vehicle.getPosition3D(v_id)
                except AttributeError:
                    # TraCI cũ không có getPosition3D
                    position = traci.vehicle.getPosition(v_id)
                speed = traci.vehicle.getSpeed(v_id)
                angle = traci.vehicle.getAngle(v_id)
                radian = math.radians(angle)
                forward = [math.cos(radian), math.sin(radian)]
                t = TrafficerData(v_id, "vehicle", speed, position, forward)
                trafficers.append(t.to_dict())
            except Exception as e:
                print(f"Error reading vehicle {v_id}: {e}")
    except Exception as e:
        print(f"Error reading vehicles from SUMO: {e}")

    # Read pedestrians. TraCI không có person.getPosition3D — suy Z bằng cách
    # nội suy theo shape của lane (đọc từ net.xml) tại vị trí dọc lane.
    try:
        ped_ids = traci.person.getIDList()
        for p_id in ped_ids:
            try:
                pos2d = traci.person.getPosition(p_id)
                z: float | None = None
                try:
                    lane_id = traci.person.getLaneID(p_id)
                    lane_pos = traci.person.getLanePosition(p_id)
                    if lane_id:
                        z = get_z_at_lane_pos(lane_id, lane_pos)
                except Exception:
                    z = None
                position = (pos2d[0], pos2d[1], z) if z is not None else pos2d
                speed = traci.person.getSpeed(p_id)
                angle = traci.person.getAngle(p_id)
                radian = math.radians(angle)
                forward = [math.cos(radian), math.sin(radian)]
                t = TrafficerData(p_id, "pedestrian", speed, position, forward)
                trafficers.append(t.to_dict())
            except Exception as e:
                print(f"Error reading pedestrian {p_id}: {e}")
    except Exception as e:
        pass

    return trafficers
