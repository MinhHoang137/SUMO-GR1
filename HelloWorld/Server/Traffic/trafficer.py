import json
import math

class TrafficerData:
    def __init__(self, id, obj_type, speed, position, forward):
        self.id = id
        self.type = obj_type
        self.speed = speed
        self.position = position
        self.forward = forward

    def to_dict(self):
        short_type = "v" if self.type == "vehicle" else "p" if self.type == "pedestrian" else self.type
        return {
            "i": self.id,
            "t": short_type,
            "sp": round(self.speed, 2),
            "p": [round(self.position[0], 2), round(self.position[1], 2)],
            "f": [round(self.forward[0], 2), round(self.forward[1], 2)]
        }

def read_trafficers(traci):
    trafficers = []
    
    # Read vehicles
    try:
        vehicle_ids = traci.vehicle.getIDList()
        for v_id in vehicle_ids:
            try:
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

    # Read pedestrians
    try:
        ped_ids = traci.person.getIDList()
        for p_id in ped_ids:
            try:
                position = traci.person.getPosition(p_id)
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
