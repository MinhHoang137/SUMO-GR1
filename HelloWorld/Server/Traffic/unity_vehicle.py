import socket
import json
import math
import threading
import os
import random
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

latest_vehicles = None
vehicles_lock = threading.Lock()
managed_ids = set()  # id xe đang do client chi phối (mirror/freeze) — dùng để reconcile khi vắng khỏi batch
wrecked_ids = set()  # id xe đang ở trạng thái Wrecked — để tô màu cam một lần

SNAP_THRESHOLD = 1000  # m: khoảng cách tối đa cho phép snap xe về lane khi re-anchor


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

def _lane_pos_to_xy(traci, lane_id: str, pos: float):
    """Nội suy toạ độ XY từ vị trí dọc theo lane (dùng shape của lane)."""
    shape = traci.lane.getShape(lane_id)
    accumulated = 0.0
    for i in range(len(shape) - 1):
        ax, ay = shape[i]
        bx, by = shape[i + 1]
        seg = math.sqrt((bx - ax) ** 2 + (by - ay) ** 2)
        if seg <= 0:
            continue
        if accumulated + seg >= pos:
            t = (pos - accumulated) / seg
            return ax + t * (bx - ax), ay + t * (by - ay)
        accumulated += seg
    return shape[-1]  # quá cuối lane → trả điểm cuối


def _find_long_route(traci, from_edge: str, min_edges: int = 3, max_attempts: int = 30):
    """Tìm tuyến đường có ít nhất min_edges cạnh từ from_edge.

    Thử ngẫu nhiên tối đa max_attempts cạnh đích; trả về list[str] hoặc None nếu không tìm được.
    """
    all_edges = [e for e in traci.edge.getIDList() if not e.startswith(':') and e != from_edge]
    candidates = random.sample(all_edges, min(max_attempts, len(all_edges)))
    for to_edge in candidates:
        try:
            result = traci.simulation.findRoute(from_edge, to_edge)
            if result and len(result.edges) >= min_edges:
                return list(result.edges)
        except Exception:
            continue
    return None


def _remove_vehicle(traci, veh_id: str):
    try:
        if veh_id in traci.vehicle.getIDList():
            traci.vehicle.remove(veh_id)
            print(f"  [-] Hủy xe {veh_id}")
    except Exception as e:
        print(f"  [!] Lỗi hủy xe {veh_id}: {e}")


def _re_anchor(traci, veh_id: str, pos: list):
    """Snap xe về lane gần nhất, cấp route, trả autopilot. Xóa xe nếu không snap được."""
    if veh_id not in traci.vehicle.getIDList():
        return
    x, y = pos[0], pos[1]

    try:
        edge_id, lane_pos, lane_idx = traci.simulation.convertRoad(x, y, isGeo=False, vClass="passenger")
    except Exception as e:
        print(f"  [!] convertRoad lỗi cho {veh_id}: {e}")
        _remove_vehicle(traci, veh_id)
        return

    if not edge_id:
        print(f"  [~] Re-anchor {veh_id}: không tìm được lane → hủy xe")
        _remove_vehicle(traci, veh_id)
        return

    lane_id = f"{edge_id}_{lane_idx}"
    try:
        sx, sy = _lane_pos_to_xy(traci, lane_id, lane_pos)
    except Exception:
        sx, sy = x, y  # fallback: dùng vị trí Unity làm gốc so sánh

    dist = math.sqrt((x - sx) ** 2 + (y - sy) ** 2)
    if dist > SNAP_THRESHOLD:
        print(f"  [~] Re-anchor {veh_id}: quá xa ({dist:.1f}m > {SNAP_THRESHOLD}m) → hủy xe")
        _remove_vehicle(traci, veh_id)
        return

    try:
        traci.vehicle.moveTo(veh_id, lane_id, lane_pos)
        route_edges = _find_long_route(traci, edge_id, min_edges=3)
        if route_edges:
            traci.vehicle.setRoute(veh_id, route_edges)
            print(f"  [<] Route {len(route_edges)} cạnh: {route_edges[0]} … {route_edges[-1]}")
        else:
            traci.vehicle.rerouteTraveltime(veh_id)
            print(f"  [<] Route fallback rerouteTraveltime")
        traci.vehicle.setSpeedMode(veh_id, 31)
        traci.vehicle.setLaneChangeMode(veh_id, 1621)
        traci.vehicle.setSpeed(veh_id, -1)
        traci.vehicle.setColor(veh_id, (255, 255, 0, 255))  # vàng: trả về server
        print(f"  [<] Re-anchor {veh_id} → {lane_id} pos {lane_pos:.1f} (dist {dist:.1f}m) → vàng")
    except Exception as e:
        print(f"  [!] Re-anchor lỗi {veh_id}: {e}")
        _remove_vehicle(traci, veh_id)


def client_handler(client_socket: socket.socket):
    global latest_vehicles
    print(f"[Python] Kết nối từ: {client_socket.getpeername()}")
    with client_socket:
        while True:
            data_str = network.receive_data(client_socket)
            if not data_str:
                break
            try:
                vehicles = json.loads(data_str)
                with vehicles_lock:
                    latest_vehicles = vehicles
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

    global latest_vehicles, managed_ids, wrecked_ids
    vehicles = None
    with vehicles_lock:
        if latest_vehicles is not None:
            vehicles = latest_vehicles
            latest_vehicles = None  # Consume the latest data

    if vehicles is not None:
        present_ids = set()
        if vehicles:
            print(f"[Python] Đang cập nhật {len(vehicles)} xe:")

        for v in vehicles:
            try:
                veh_id = v['i']
                # ExistState: 0 = Destroyed, 1 = ServerControlled (re-anchor — chunk 5),
                # 2 = ClientControlled (client lái, SUMO mirror), 3 = Wrecked (xác xe đông cứng).
                state = v.get('e', 1)

                # Hết vòng đời → remove khỏi SUMO
                if state == 0:
                    if veh_id in traci.vehicle.getIDList():
                        try:
                            traci.vehicle.remove(veh_id)
                            print(f"  [-] Xoá xe {veh_id} khỏi SUMO")
                        except Exception as e:
                            print(f"  [!] Lỗi khi xoá xe {veh_id}: {e}")
                    wrecked_ids.discard(veh_id)
                    continue  # Không xử lý thêm

                pos = v['p']
                forward = v['f']
                speed = v['sp']
                angle = math.degrees(math.atan2(forward[0], forward[1]))

                # state 1 = re-anchor (chunk 5): thả quyền → snap về lane, cấp route, trả autopilot.
                # Không add vào present_ids → reconcile không đụng sau khi managed_ids.discard.
                if state == 1:
                    _re_anchor(traci, veh_id, pos)
                    managed_ids.discard(veh_id)
                    wrecked_ids.discard(veh_id)
                    continue

                # Xe client chưa có gốc trong SUMO (vd CLIENT_CAR) → thêm mới (đỏ).
                # Xe server bị chiếm quyền thì đã có sẵn → bỏ qua add, đổi sang xanh lam.
                was_added = False
                if veh_id not in traci.vehicle.getIDList():
                    try:
                        traci.vehicle.add(vehID=veh_id, routeID="", typeID="DEFAULT_VEHTYPE")
                        traci.vehicle.setColor(veh_id, (255, 0, 0, 255))  # đỏ: do Unity sinh
                        print(f"  [+] Thêm xe mới: {veh_id}")
                        was_added = True
                    except Exception as e:
                        print(f"  [!] Lỗi khi thêm xe {veh_id}: {e}")
                        continue

                # Xe server bị chiếm quyền lần đầu (đã có sẵn, chưa từng quản lý) → xanh lam, set 1 lần.
                if not was_added and veh_id not in managed_ids:
                    traci.vehicle.setColor(veh_id, (0, 0, 255, 255))  # xanh lam: bị chiếm quyền
                    print(f"  [~] Xe {veh_id} bị chiếm quyền → xanh lam")

                present_ids.add(veh_id)  # đang do client chi phối → reconcile sẽ giữ

                # Tắt autopilot để SUMO không giành lái xe đang do client chi phối.
                traci.vehicle.setSpeedMode(veh_id, 0)
                traci.vehicle.setLaneChangeMode(veh_id, 0)

                if state == 3:
                    # Xác xe: đông cứng tại chỗ → các xe sau dồn lại gây ùn ứ.
                    # Despawn do client điều khiển (gửi state 0 khi hết N bước).
                    traci.vehicle.setSpeed(veh_id, 0)
                    if veh_id not in wrecked_ids:
                        traci.vehicle.setColor(veh_id, (255, 165, 0, 255))  # cam: xác xe
                        wrecked_ids.add(veh_id)
                        print(f"  [x] Xe {veh_id} thành xác → cam, đông cứng tại {pos}")
                    continue

                # state 2 (mirror) — SUMO bám theo vị trí client lái.
                # state 1 (re-anchor) sẽ xử lý riêng ở chunk 5; uploader hiện chỉ gửi 2/3.
                traci.vehicle.moveToXY(vehID=veh_id,
                                       edgeID="", laneIndex=0,
                                       x=pos[0], y=pos[1],
                                       angle=angle, keepRoute=0)

                traci.vehicle.setSpeed(veh_id, speed)

                # Cập nhật tín hiệu rẽ trái / rẽ phải / phanh
                # turn_left = v.get("turnLeft", False)
                # turn_right = v.get("turnRight", False)
                # is_braking = v.get("isBraking", False)

                # signal_value = 0
                # if turn_left:
                #     signal_value |= 0b00000001
                # if turn_right:
                #     signal_value |= 0b00000010
                # if is_braking:
                #     signal_value |= 0b00000100

                # traci.vehicle.setSignals(veh_id, signal_value)

                print(f"  [>] Di chuyển {veh_id} đến {pos} | góc {angle:.2f} | tốc độ {speed}")

            except Exception as e:
                print(f"  [!] Lỗi khi cập nhật xe {v.get('id', '?')}: {e}")

        # Reconcile: xe từng do client chi phối nhưng vắng khỏi batch (client thả/huỷ/despawn) → xoá khỏi SUMO.
        for gone in managed_ids - present_ids:
            if gone in traci.vehicle.getIDList():
                try:
                    traci.vehicle.remove(gone)
                    print(f"  [-] Reconcile: xoá {gone} khỏi SUMO")
                except Exception as e:
                    print(f"  [!] Lỗi reconcile xoá {gone}: {e}")
            wrecked_ids.discard(gone)
        managed_ids = present_ids
