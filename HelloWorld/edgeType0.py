import os
import json
import xml.etree.ElementTree as ET

NET_XML_PATH = os.path.join(os.path.dirname(__file__), 'HelloWorld.net.xml')
OUTPUT_FILE = './TestGR1.1/Assets/Scripts/SumoData/edge.json'


def parse_shape(shape):
    points = shape.strip().split(' ')
    vertices = [(float(p.split(',')[0]), float(p.split(',')[1])) for p in points]
    return vertices


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
                # Làn đi bộ
                walking_lanes[index] = vertices
            elif 'disallow' in lane.attrib and 'pedestrian' in lane.get('disallow'):
                # Làn xe
                road_lanes[index] = vertices
            else:
                # Mặc định là làn xe nếu không có 'allow' hoặc 'disallow'
                road_lanes[index] = vertices

        # ✅ Chọn làn bên trái cùng (làn có index lớn nhất)
        start_road_lane = road_lanes[max(road_lanes.keys())][0] if road_lanes else None
        end_road_lane = road_lanes[max(road_lanes.keys())][-1] if road_lanes else None
        start_walking_lane = walking_lanes[max(walking_lanes.keys())][0] if walking_lanes else None
        end_walking_lane = walking_lanes[max(walking_lanes.keys())][-1] if walking_lanes else None

        # ✅ Tính hướng di chuyển
        if start_road_lane and end_road_lane:
            direction_x = end_road_lane[0] - start_road_lane[0]
            direction_y = end_road_lane[1] - start_road_lane[1]
            direction = {"x": direction_x, "y": direction_y}
            position = {
                "x": (start_road_lane[0] + end_road_lane[0]) / 2,
                "y": (start_road_lane[1] + end_road_lane[1]) / 2
            }
        else:
            direction = None
            position = None

        edge_data = {
            "id": edge_id,
            "startRoadLane": {
                "x": start_road_lane[0], "y": start_road_lane[1]
            } if start_road_lane else None,
            "endRoadLane": {
                "x": end_road_lane[0], "y": end_road_lane[1]
            } if end_road_lane else None,
            "roadNum": len(road_lanes),
            "startWalkingLane": {
                "x": start_walking_lane[0], "y": start_walking_lane[1]
            } if start_walking_lane else None,
            "endWalkingLane": {
                "x": end_walking_lane[0], "y": end_walking_lane[1]
            } if end_walking_lane else None,
            "walkingNum": len(walking_lanes),
            "direction": direction,
            "position": position
        }

        edges.append(edge_data)

    if edges:
        with open(OUTPUT_FILE, 'w', encoding='utf-8-sig') as f:
            json.dump(edges, f, indent=4, ensure_ascii=False)
        print(f"Edges data saved to {OUTPUT_FILE}")
    else:
        print("No valid edges found.")

if __name__ == "__main__":
    read_edges()
