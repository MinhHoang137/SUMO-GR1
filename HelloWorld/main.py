import traci
import json
import os
import time
import xml.etree.ElementTree as ET
from math import atan2

# ✅ Lớp cha TrafficerData
class TrafficerData:
    def __init__(self, id, type, position, speed, lane):
        self.id = id
        self.type = type
        self.position = position
        self.speed = speed
        self.lane = lane

    def to_dict(self):
        return {
            "id": self.id,
            "type": self.type,
            "position": self.position,
            "speed": self.speed,
            "lane": self.lane
        }


# Đường dẫn đến các file
NET_XML_PATH = os.path.join(os.path.dirname(__file__), 'HelloWorld.net.xml')
OUTPUT_FILE_JUNCTION = './TestGR1.1/Assets/Scripts/SumoData/CrossRoad.json'
OUTPUT_FILE_EDGE = './TestGR1.1/Assets/Scripts/SumoData/edge.json'
OUTPUT_FILE = './TestGR1.1/Assets/Scripts/SumoData/HelloWorld.json'
LOCK_FILE = './TestGR1.1/Assets/Scripts/SumoData/lock.tmp'


# ======== Đọc dữ liệu từ file XML ========
def parse_shape(shape):
    points = shape.strip().split(' ')
    vertices = [(float(p.split(',')[0]), float(p.split(',')[1])) for p in points]
    return vertices


def sort_clockwise(vertices):
    if not vertices:
        return []
    center_x = sum(v[0] for v in vertices) / len(vertices)
    center_y = sum(v[1] for v in vertices) / len(vertices)
    sorted_vertices = sorted(vertices, key=lambda v: atan2(v[1] - center_y, v[0] - center_x), reverse=True)
    return sorted_vertices


# ✅ Đọc dữ liệu từ junction
def read_all_junctions():
    if not os.path.exists(NET_XML_PATH):
        print(f"Error: {NET_XML_PATH} does not exist.")
        return

    tree = ET.parse(NET_XML_PATH)
    root = tree.getroot()

    crossroads = []
    for junction in root.findall('junction'):
        junction_id = junction.get('id')
        junction_type = junction.get('type', 'unknown')
        x = float(junction.get('x'))
        y = float(junction.get('y'))
        shape = junction.get('shape')

        if shape:
            vertices = parse_shape(shape)
            sorted_vertices = sort_clockwise(vertices)
            crossroad = {
                "id": junction_id,
                "type": junction_type,
                "position": [x, y],
                "vertices": [{"x": v[0], "y": v[1]} for v in sorted_vertices]
            }
            crossroads.append(crossroad)

    if crossroads:
        with open(OUTPUT_FILE_JUNCTION, 'w', encoding='utf-8-sig') as f:
            json.dump(crossroads, f, indent=4, ensure_ascii=False)
        print(f"Junctions data saved to {OUTPUT_FILE_JUNCTION}")


# ✅ Đọc dữ liệu từ edge
def read_edges():
    if not os.path.exists(NET_XML_PATH):
        print(f"Error: {NET_XML_PATH} does not exist.")
        return

    tree = ET.parse(NET_XML_PATH)
    root = tree.getroot()

    edges = []
    for edge in root.findall('edge'):
        edge_type = edge.get('type')
        if edge_type != 'edgeType_0':
            continue

        edge_id = edge.get('id')
        road_lanes = {}
        walking_lanes = {}

        for lane in edge.findall('lane'):
            shape = lane.get('shape')
            if not shape:
                continue

            index = int(lane.get('index'))
            vertices = parse_shape(shape)

            if 'allow' in lane.attrib and 'pedestrian' in lane.get('allow'):
                walking_lanes[index] = vertices
            elif 'disallow' in lane.attrib and 'pedestrian' in lane.get('disallow'):
                road_lanes[index] = vertices
            else:
                road_lanes[index] = vertices

        start_road_lane = road_lanes[max(road_lanes.keys())][0] if road_lanes else None
        end_road_lane = road_lanes[max(road_lanes.keys())][-1] if road_lanes else None
        start_walking_lane = walking_lanes[max(walking_lanes.keys())][0] if walking_lanes else None
        end_walking_lane = walking_lanes[max(walking_lanes.keys())][-1] if walking_lanes else None

        if start_road_lane and end_road_lane:
            direction = {
                "x": end_road_lane[0] - start_road_lane[0],
                "y": end_road_lane[1] - start_road_lane[1]
            }
            position = {
                "x": (start_road_lane[0] + end_road_lane[0]) / 2,
                "y": (start_road_lane[1] + end_road_lane[1]) / 2
            }
        else:
            direction = None
            position = None

        edge_data = {
            "id": edge_id,
            "startRoadLane": {"x": start_road_lane[0], "y": start_road_lane[1]} if start_road_lane else None,
            "endRoadLane": {"x": end_road_lane[0], "y": end_road_lane[1]} if end_road_lane else None,
            "roadNum": len(road_lanes),
            "startWalkingLane": {"x": start_walking_lane[0],
                                 "y": start_walking_lane[1]} if start_walking_lane else None,
            "endWalkingLane": {"x": end_walking_lane[0], "y": end_walking_lane[1]} if end_walking_lane else None,
            "walkingNum": len(walking_lanes),
            "direction": direction,
            "position": position
        }
        edges.append(edge_data)

    if edges:
        with open(OUTPUT_FILE_EDGE, 'w', encoding='utf-8-sig') as f:
            json.dump(edges, f, indent=4, ensure_ascii=False)
        print(f"Edges data saved to {OUTPUT_FILE_EDGE}")


# ✅ Khởi tạo mô phỏng
def run_simulation():
    traci.start(["sumo-gui", "-c", "HelloWorld.sumocfg"])

    while traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep()

        # ✅ Tạo file khóa để Unity không đọc khi Python đang ghi
        open(LOCK_FILE, "w").close()

        traffickers = []

        # ✅ Lấy dữ liệu từ SUMO cho xe cộ và người đi bộ
        for veh_id in traci.vehicle.getIDList():
            trafficker = TrafficerData(
                id=veh_id,
                type="Car",
                position=traci.vehicle.getPosition(veh_id),
                speed=traci.vehicle.getSpeed(veh_id),
                lane=traci.vehicle.getLaneID(veh_id)
            )
            traffickers.append(trafficker.to_dict())

        for ped_id in traci.person.getIDList():
            trafficker = TrafficerData(
                id=ped_id,
                type="Pedestrian",
                position=traci.person.getPosition(ped_id),
                speed=traci.person.getSpeed(ped_id),
                lane=traci.person.getLaneID(ped_id)
            )
            traffickers.append(trafficker.to_dict())

        try:
            with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
                json.dump(traffickers, file, indent=4)
        except Exception as e:
            print(f"❌ Error writing JSON: {e}")

        # ✅ Xóa file khóa
        os.remove(LOCK_FILE)

        time.sleep(0.1)  # Nghỉ 0.1 giây giữa các bước mô phỏng

    traci.close()

# ======== MAIN ========
if __name__ == "__main__":
    print("🔹 Reading junctions...")
    read_all_junctions()

    print("🔹 Reading edges...")
    read_edges()

    print("🔹 Starting simulation...")
    run_simulation()

    print("✅ Simulation completed!")
