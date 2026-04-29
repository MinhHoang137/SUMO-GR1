import socket
import json
import math
from queue import Queue
import os
import xml.etree.ElementTree as ET
import network

HOST = '127.0.0.1'
PORT = 5053
END_MARKER = '<END>'
ROUTE_ID = "unity_temp_route"
# Sẽ chọn EDGE_ID động từ .net.xml / TraCI (không hard-code)
EDGE_ID = None

# Đường dẫn mặc định tới mạng SUMO sinh ra bởi mã
DEFAULT_NET_PATH = os.path.join(os.path.dirname(__file__), '../SUMO_xml/HelloWorld.net.xml')

update_queue = Queue()


def _pick_edge_from_netxml(net_xml_path: str) -> str:
    """Chọn cạnh mặc định từ .net.xml.

    Ưu tiên cạnh có priority="-1" và có lane dành cho xe (không chỉ pedestrian).
    Nếu không có, chọn cạnh hợp lệ bất kỳ (không phải cạnh nội bộ bắt đầu bằng ':').

    Trả về: edge id hoặc "" nếu không tìm thấy.
    """
    try:
        if not os.path.isfile(net_xml_path):
            return ""

        tree = ET.parse(net_xml_path)
        root = tree.getroot()

        def is_vehicle_lane(lane_elem: ET.Element) -> bool:
            dis = lane_elem.attrib.get("disallow", "")
            allow = lane_elem.attrib.get("allow", "")
            if "pedestrian" in dis:
                return True
            if allow.strip() == "pedestrian":
                return False
            return True

        # 1) Ưu tiên cạnh priority="-1"
        for edge in root.findall("edge"):
            eid = edge.attrib.get("id", "")
            if not eid or eid.startswith(":"):
                continue
            if edge.attrib.get("priority") == "-1":
                lanes = edge.findall("lane")
                if any(is_vehicle_lane(ln) for ln in lanes):
                    return eid

        # 2) Fallback: cạnh hợp lệ bất kỳ
        for edge in root.findall("edge"):
            eid = edge.attrib.get("id", "")
            if not eid or eid.startswith(":"):
                continue
            lanes = edge.findall("lane")
            if any(is_vehicle_lane(ln) for ln in lanes):
                return eid

        return ""
    except Exception:
        return ""

def client_handler(client_socket : socket.socket):
    print(f"[Python] Kết nối từ: {client_socket.getpeername()}")
    with client_socket:
        while True:
            data_str = network.receive_data(client_socket)
            if not data_str:
                break
            try:
                vehicles = json.loads(data_str)
                update_queue.put(vehicles)
            except json.JSONDecodeError as e:
                print(f"[Python] Lỗi phân tích JSON: {e}")
            except Exception as e:
                print(f"[Python] Lỗi xử lý dữ liệu: {e}")
    print("[Python] Client đã đóng kết nối.")

def receive(vehicle_socket):
    network.server_thread(vehicle_socket, client_handler)


def process_vehicle_updates(traci):
    """Cập nhật xe trong SUMO dựa trên dữ liệu từ Unity."""
    global EDGE_ID

    # Chọn cạnh mặc định từ .net.xml (ưu tiên priority=-1), nếu không có thì fallback sang danh sách trong TraCI
    if EDGE_ID is None or EDGE_ID not in traci.edge.getIDList():
        picked = _pick_edge_from_netxml(DEFAULT_NET_PATH)
        if picked:
            EDGE_ID = picked
        else:
            all_edges = traci.edge.getIDList()
            candidate_edges = [e for e in all_edges if not e.startswith(':')]
            EDGE_ID = candidate_edges[0] if candidate_edges else ""

        if EDGE_ID:
            print(f"[Python] EDGE_ID mặc định được chọn: {EDGE_ID}")
        else:
            print("[Python] Không tìm thấy cạnh hợp lệ trong mạng để tạo route.")

    if ROUTE_ID not in traci.route.getIDList() and EDGE_ID:
        traci.route.add(ROUTE_ID, [EDGE_ID])
        print(f"[Python] Đã tạo route {ROUTE_ID} -> {EDGE_ID}")

    while not update_queue.empty():
        vehicles = update_queue.get()
        print(f"[Python] Đang cập nhật {len(vehicles)} xe:")

        for v in vehicles:
            try:
                veh_id = v['id']
                is_exist = v.get('isExist', True)

                # Nếu Unity đã xoá xe, thì remove khỏi SUMO
                if not is_exist:
                    if veh_id in traci.vehicle.getIDList():
                        try:
                            traci.vehicle.remove(veh_id)
                            print(f"  [-] Xoá xe {veh_id} khỏi SUMO")
                        except Exception as e:
                            print(f"  [!] Lỗi khi xoá xe {veh_id}: {e}")
                    continue  # Không xử lý thêm

                pos = v['position']
                forward = v['forward']
                speed = v['speed']
                angle = math.degrees(math.atan2(forward[0], forward[1]))

                if veh_id not in traci.vehicle.getIDList():
                    try:
                        traci.vehicle.add(vehID=veh_id, routeID="", typeID="DEFAULT_VEHTYPE")
                        traci.vehicle.setColor(veh_id, (255, 0, 0, 255))
                        traci.vehicle.setLaneChangeMode(veh_id, 0b000000000000)
                        print(f"  [+] Thêm xe mới: {veh_id}")
                    except Exception as e:
                        print(f"  [!] Lỗi khi thêm xe {veh_id}: {e}")
                        continue

                traci.vehicle.moveToXY(vehID=veh_id,
                                       edgeID="", laneIndex=0,
                                       x=pos[0], y=pos[1],
                                       angle=angle, keepRoute=0)

                traci.vehicle.setSpeed(veh_id, speed)

                # Cập nhật tín hiệu rẽ trái / rẽ phải / phanh
                turn_left = v.get("turnLeft", False)
                turn_right = v.get("turnRight", False)
                is_braking = v.get("isBraking", False)

                signal_value = 0
                if turn_left:
                    signal_value |= 0b00000001
                if turn_right:
                    signal_value |= 0b00000010
                if is_braking:
                    signal_value |= 0b00000100

                traci.vehicle.setSignals(veh_id, signal_value)

                print(f"  [>] Di chuyển {veh_id} đến {pos} | góc {angle:.2f} | tốc độ {speed} | tín hiệu: {bin(signal_value)}")

            except Exception as e:
                print(f"  [!] Lỗi khi cập nhật xe {v.get('id', '?')}: {e}")
