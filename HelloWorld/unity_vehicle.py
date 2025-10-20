import socket
import json
import math
from queue import Queue

HOST = '127.0.0.1'
PORT = 5053
END_MARKER = '<END>'
ROUTE_ID = "unity_temp_route"
EDGE_ID = "E3"

update_queue = Queue()

def receive():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind((HOST, PORT))
        server_socket.listen()
        print(f"[Python] Đang lắng nghe dữ liệu từ Unity tại {HOST}:{PORT}...")

        while True:
            conn, addr = server_socket.accept()
            with conn:
                print(f"[Python] Kết nối từ: {addr}")
                full_data = ''
                while True:
                    data = conn.recv(4096).decode('utf-8')
                    if not data:
                        break
                    full_data += data
                    if END_MARKER in full_data:
                        break

                try:
                    json_data = full_data.replace(END_MARKER, '').strip()
                    vehicles = json.loads(json_data)
                    update_queue.put(vehicles)  # Đẩy vào hàng đợi để xử lý sau
                except json.JSONDecodeError as e:
                    print(f"[Python] Lỗi phân tích JSON: {e}")
                except Exception as e:
                    print(f"[Python] Lỗi xử lý dữ liệu: {e}")


def process_vehicle_updates(traci):
    """Cập nhật xe trong SUMO dựa trên dữ liệu từ Unity."""

    if ROUTE_ID not in traci.route.getIDList():
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
