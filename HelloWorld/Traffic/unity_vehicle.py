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

# Keep the latest received Unity frame so throttling (unityEvery) doesn't drop it.
_latest_frame = None

# Cache to reduce TraCI round-trips (which are usually the main cost).
# last_state[veh_id] = (x, y, angle, speed, signals)
_last_state = {}

# Tuning knobs (can be controlled from main via setters)
_apply_every_n_steps = 1
_step_counter = 0
_apply_speed = True
_apply_signals = True


def set_apply_every(n_steps: int) -> None:
    """Apply Unity updates every N simulation steps (>=1)."""
    global _apply_every_n_steps
    try:
        n = int(n_steps)
    except Exception:
        return
    _apply_every_n_steps = max(1, n)


def set_apply_speed(enabled: bool) -> None:
    global _apply_speed
    _apply_speed = bool(enabled)


def set_apply_signals(enabled: bool) -> None:
    global _apply_signals
    _apply_signals = bool(enabled)


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

    global _step_counter
    global _latest_frame
    _step_counter += 1
    if (_step_counter % _apply_every_n_steps) != 0:
        # Drain backlog but keep the newest frame for the next apply step.
        while not update_queue.empty():
            try:
                _latest_frame = update_queue.get_nowait()
            except Exception:
                break
        return

    # Chọn cạnh mặc định 1 lần (tránh gọi traci.edge.getIDList() mỗi step)
    if EDGE_ID is None:
        picked = _pick_edge_from_netxml(DEFAULT_NET_PATH)
        if picked:
            EDGE_ID = picked
        else:
            try:
                all_edges = traci.edge.getIDList()
                candidate_edges = [e for e in all_edges if not e.startswith(':')]
                EDGE_ID = candidate_edges[0] if candidate_edges else ""
            except Exception:
                EDGE_ID = ""

        if not EDGE_ID:
            print("[Python] Không tìm thấy cạnh hợp lệ trong mạng để tạo route.")

    if ROUTE_ID not in traci.route.getIDList() and EDGE_ID:
        traci.route.add(ROUTE_ID, [EDGE_ID])

    # Pull newest frame from queue (if any); otherwise reuse last stored frame.
    vehicles = None
    while not update_queue.empty():
        try:
            vehicles = update_queue.get_nowait()
        except Exception:
            break
    if vehicles is not None:
        _latest_frame = vehicles
    else:
        vehicles = _latest_frame

    if not vehicles:
        return

    # One TraCI call per step (not per vehicle)
    try:
        sumo_vehicle_ids = set(traci.vehicle.getIDList())
    except Exception:
        sumo_vehicle_ids = set()

    for v in vehicles:
        try:
            veh_id = v['id']
            is_exist = v.get('isExist', True)

            # Nếu Unity đã xoá xe, thì remove khỏi SUMO
            if not is_exist:
                if veh_id in sumo_vehicle_ids:
                    try:
                        traci.vehicle.remove(veh_id)
                        sumo_vehicle_ids.discard(veh_id)
                        _last_state.pop(veh_id, None)
                    except Exception as e:
                        print(f"  [!] Lỗi khi xoá xe {veh_id}: {e}")
                continue  # Không xử lý thêm

            pos = v['position']
            forward = v['forward']
            speed = v.get('speed', 0.0)
            angle = math.degrees(math.atan2(forward[0], forward[1]))

            if veh_id not in sumo_vehicle_ids:
                try:
                    # Prefer a valid route if we have one; SUMO can reject vehicles without a route.
                    route_id = ROUTE_ID if (EDGE_ID and ROUTE_ID in traci.route.getIDList()) else ""
                    traci.vehicle.add(vehID=veh_id, routeID=route_id, typeID="DEFAULT_VEHTYPE")
                    traci.vehicle.setColor(veh_id, (255, 0, 0, 255))
                    traci.vehicle.setLaneChangeMode(veh_id, 0b000000000000)
                    sumo_vehicle_ids.add(veh_id)
                except Exception as e:
                    print(f"  [!] Lỗi khi thêm xe {veh_id}: {e}")
                    continue

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

            # Skip commands if nothing changed (reduces TraCI calls a lot)
            prev = _last_state.get(veh_id)
            x, y = float(pos[0]), float(pos[1])
            a = float(angle)
            s = float(speed)
            sig = int(signal_value)

            # NOTE: moveToXY is usually the heaviest call. We only call it when pose changed.
            if prev is None or (abs(prev[0] - x) > 1e-4 or abs(prev[1] - y) > 1e-4 or abs(prev[2] - a) > 1e-3):
                traci.vehicle.moveToXY(
                    vehID=veh_id,
                    edgeID="",
                    laneIndex=0,
                    x=x,
                    y=y,
                    angle=a,
                    keepRoute=0,
                )

            if _apply_speed and (prev is None or abs(prev[3] - s) > 1e-3):
                traci.vehicle.setSpeed(veh_id, s)

            if _apply_signals and (prev is None or prev[4] != sig):
                traci.vehicle.setSignals(veh_id, sig)

            # Store full state even if speed/signals disabled so pose dedupe still works.
            _last_state[veh_id] = (x, y, a, s, sig)

        except Exception as e:
            print(f"  [!] Lỗi khi cập nhật xe {v.get('id', '?')}: {e}")
