import math

import traci.constants as tc

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


# --- TraCI subscriptions ---------------------------------------------------
# Thay vì gọi getPosition/getSpeed/getAngle riêng cho từng đối tượng mỗi step
# (N×k round-trip TraCI), ta SUBSCRIBE mỗi đối tượng đúng 1 lần rồi mỗi step chỉ
# getAllSubscriptionResults() — gom toàn bộ trong ~1 round-trip. SUMO tự xoá
# subscription khi đối tượng rời mô phỏng; ta chỉ cần đồng bộ tập đã subscribe.
_VEHICLE_VARS = (tc.VAR_POSITION3D, tc.VAR_SPEED, tc.VAR_ANGLE)
_PERSON_VARS = (tc.VAR_POSITION, tc.VAR_SPEED, tc.VAR_ANGLE, tc.VAR_LANE_ID, tc.VAR_LANEPOSITION)

_subscribed_vehicles: set[str] = set()
_subscribed_persons: set[str] = set()


def _sync_subscriptions(domain, current_ids, subscribed: set, vars) -> None:
    """Subscribe đối tượng mới xuất hiện; tỉa khỏi set những id đã rời mô phỏng.

    Subscribe gửi luôn response chứa giá trị hiện tại nên getAllSubscriptionResults()
    ngay sau đó đã có dữ liệu của đối tượng vừa subscribe (không trễ 1 step)."""
    current = set(current_ids)
    for obj_id in current - subscribed:
        try:
            domain.subscribe(obj_id, vars)
            subscribed.add(obj_id)
        except Exception as e:
            print(f"Error subscribing {obj_id}: {e}")
    # Đối tượng đã rời: SUMO tự huỷ subscription → chỉ cần tỉa khỏi set cục bộ.
    subscribed.intersection_update(current)


def read_trafficers(traci):
    trafficers = []

    # --- Vehicles (dùng position3D để có cao độ — cần cho cầu/đèo trong .osm) ---
    try:
        vehicle_ids = traci.vehicle.getIDList()
        _sync_subscriptions(traci.vehicle, vehicle_ids, _subscribed_vehicles, _VEHICLE_VARS)
        results = traci.vehicle.getAllSubscriptionResults()
        for v_id in vehicle_ids:
            try:
                res = results.get(v_id)
                if res is None:
                    # Hiếm: chưa có kết quả subscription → đọc trực tiếp (an toàn).
                    position = traci.vehicle.getPosition3D(v_id)
                    speed = traci.vehicle.getSpeed(v_id)
                    angle = traci.vehicle.getAngle(v_id)
                else:
                    position = res[tc.VAR_POSITION3D]
                    speed = res[tc.VAR_SPEED]
                    angle = res[tc.VAR_ANGLE]
                radian = math.radians(angle)
                forward = [math.cos(radian), math.sin(radian)]
                t = TrafficerData(v_id, "vehicle", speed, position, forward)
                trafficers.append(t.to_dict())
            except Exception as e:
                print(f"Error reading vehicle {v_id}: {e}")
    except Exception as e:
        print(f"Error reading vehicles from SUMO: {e}")

    # --- Pedestrians. TraCI person không có position3D — suy Z bằng cách nội suy
    #     theo shape của lane (đọc từ net.xml) tại vị trí dọc lane. ---
    try:
        ped_ids = traci.person.getIDList()
        _sync_subscriptions(traci.person, ped_ids, _subscribed_persons, _PERSON_VARS)
        results = traci.person.getAllSubscriptionResults()
        for p_id in ped_ids:
            try:
                res = results.get(p_id)
                if res is None:
                    pos2d = traci.person.getPosition(p_id)
                    speed = traci.person.getSpeed(p_id)
                    angle = traci.person.getAngle(p_id)
                    lane_id = None
                    lane_pos = None
                    try:
                        lane_id = traci.person.getLaneID(p_id)
                        lane_pos = traci.person.getLanePosition(p_id)
                    except Exception:
                        lane_id = None
                else:
                    pos2d = res[tc.VAR_POSITION]
                    speed = res[tc.VAR_SPEED]
                    angle = res[tc.VAR_ANGLE]
                    lane_id = res.get(tc.VAR_LANE_ID)
                    lane_pos = res.get(tc.VAR_LANEPOSITION)

                z: float | None = None
                try:
                    if lane_id and lane_pos is not None:
                        z = get_z_at_lane_pos(lane_id, lane_pos)
                except Exception:
                    z = None
                position = (pos2d[0], pos2d[1], z) if z is not None else pos2d

                radian = math.radians(angle)
                forward = [math.cos(radian), math.sin(radian)]
                t = TrafficerData(p_id, "pedestrian", speed, position, forward)
                trafficers.append(t.to_dict())
            except Exception as e:
                print(f"Error reading pedestrian {p_id}: {e}")
    except Exception as e:
        pass

    return trafficers
