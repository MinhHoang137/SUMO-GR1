import json
import math
import socket
import subprocess
import sys
from time import sleep

import traci
import time
import threading
import network

from Traffic.crossing import CrossingReader
from Traffic.crossRoad import CrossRoadReader
from Traffic.edgeType0 import EdgeReader
from Traffic.trafficLight import read_traffic_lights
from Traffic.vehicle import read_vehicles
from Traffic.pedestrian import read_pedestrians
from Traffic.unity_vehicle import receive, process_vehicle_updates
from SUMO_xml.create_map_from_maze import create_map_from_maze_file
from SUMO_xml.route_gen import create_routes
from SUMO_xml.create_city_map import create_map
from naive_map_creator import naive_create_map

CS = "CS"
SS = "SS"
IO = "IO"
OI = "OI"

MAX_PACKET_SIZE = 131072 # 128 KB
MAX_RETRIES = 5
END_MARKER = '<END>'

target_exe = "./UnityBuild/TestGR1.1.exe"
stop_event = threading.Event()
time_step = 0.05  # Giả sử mỗi bước mô phỏng là 0.11 giây
time_step_lock = threading.Lock()
# Pause/resume simulation (thread-safe). Unity should control this via commands.
pause_event = threading.Event()  # set => paused, clear => running


def set_pause_sim(is_paused: bool) -> None:
    """Set pause state in a thread-safe way."""
    if bool(is_paused):
        pause_event.set()
    else:
        pause_event.clear()


def is_paused() -> bool:
    return pause_event.is_set()

HOST = '0.0.0.0'
MAIN_PORT = 5050

def async_task(target, *args, join=False, daemon=False):
    thread = threading.Thread(target=target, args=args)
    thread.daemon = daemon  # nếu True thì thread không ngăn tiến trình chính thoát
    thread.start()
    if join:
        thread.join()
    return thread


def process_config_update(data: dict):
    """
    Updates global configuration variables based on the provided dictionary.
    Only updates known parameters. Ignores negative values for numeric parameters.
    """
    # Map JSON keys to (global_variable_name, lock_object)
    # Add new parameters here as needed.
    param_map = {
        "timeStep": ("time_step", time_step_lock),
    }

    for key, value in data.items():
        if key in param_map:
            var_name, lock = param_map[key]
            try:
                # Convert to float for numeric check (assuming all current params are numeric)
                # If we have non-numeric params later, we might need type info in param_map
                val = float(value)
                
                if val < 0:
                    print(f"[Info] Ignored negative value for {key}: {val}")
                    continue

                if lock:
                    with lock:
                        globals()[var_name] = val
                else:
                    globals()[var_name] = val
                
                print(f"[Info] Updated {var_name} to {val}")
            except Exception as e:
                print(f"[Error] Failed to update {key} with value {value}: {e}")


def client_thread_function(socket: socket.socket):
    first_msg = socket.recv(1024).decode('utf-8')
    print(f"Received first message from Unity client: {first_msg}")
    if "RoadDataRequest" in first_msg:
        send_road_data(socket)
        socket.close()
    if ("SimulationReady" in first_msg):
        print("Starting simulation...")
        run_simulation(client_socket=socket)
        print("Simulation completed!")
    return 0


def cmd_handler(client_socket: socket.socket):
    """Handle control commands from a connected client in a loop.

    This keeps reading messages from the same client until the client
    closes the connection or sends `Simulation end`.
    """
    expected_msg = "Simulation end"
    try:
        # Set timeout để recv không chặn mãi mãi, cho phép thread kiểm tra điều kiện khác hoặc nhường CPU
        while True:
            try:
                msg = network.receive_message(client_socket)
            except socket.timeout:
                # Timeout xảy ra, không có dữ liệu, tiếp tục vòng lặp
                continue
            except Exception as e:
                print(f"Socket error: {e}")
                break

            if not msg:
                print("Client disconnected.")
                break
            msg = msg.strip()
            print(f"Received command: {msg}")
            
            if msg == expected_msg:
                print("Shutting down simulation as per client request.")
                stop_event.set()
                break
            elif msg == "Pause":
                set_pause_sim(True)
                print("Simulation paused.")
            elif msg == "Resume":
                set_pause_sim(False)
                print("Simulation resumed.")
            elif msg.startswith("{") and msg.endswith("}"):
                # Xử lý cấu hình JSON đơn giản
                try:
                    data = json.loads(msg)
                    if "timeStep" in data:
                        val = float(data["timeStep"])
                        if val > 0:
                            with time_step_lock:
                                global time_step
                                time_step = val/1000.0  # Chuyển từ ms sang giây
                            print(f"[Info] Updated time_step to {time_step}")
                except Exception as e:
                    print(f"[Error] Failed to process JSON config: {e}")
            else:
                print(f"[Info] Unknown command from Unity: {msg}")
            
            # Thêm sleep nhỏ để tránh chiếm dụng CPU quá mức nếu client gửi liên tục hoặc vòng lặp chạy quá nhanh
            time.sleep(0.01)

    except Exception as e:
        print(f"Error in command handler: {e}")
    finally:
        client_socket.close()

# Nhận lệnh điều khiển từ Unity (dừng, tạm dừng, tiếp tục, cập nhật cấu hình)
def listen_for_control_commands(shutdown_socket):
    network.server_thread(shutdown_socket, cmd_handler)
    return 0

# Hàm chạy mô phỏng SUMO và ghi dữ liệu
def run_simulation(client_socket: socket.socket):
    traci.start(["sumo", "-c", "./SUMO_xml/HelloWorld.sumocfg"])
    try:
        while traci.simulation.getMinExpectedNumber() > 0 and not stop_event.is_set():
            if pause_event.is_set():
                sleep(0.5)
                continue
            traci.simulationStep()
            process_vehicle_updates(traci)
            data = {
                "trafficLights": read_traffic_lights(traci),
                "vehicles": read_vehicles(traci),
                "pedestrians": read_pedestrians(traci)
            }
            async_task(network.send_data, client_socket, data, join=False)
            
            current_time_step = 0.05
            with time_step_lock:
                current_time_step = time_step
            sleep(current_time_step)

    finally:
        traci.close()
        print("SUMO simulation stopped.")

def send_road_data(client_socket: socket.socket):
    crossroads = CrossRoadReader.read_all_junctions()
    edges =  EdgeReader.read_edges()
    crossings = CrossingReader.read_crossings()
    road_data = {
        "junctionDatas": crossroads,
        "edgeDatas": edges,
        "crossingDatas": crossings
    }
    try:
        for i in range(MAX_RETRIES):
            if not network.send_data(client_socket, road_data):
                print("Retrying to send road data...")
                time.sleep(1)
            else:
                break
        print("Road data sent successfully.")
    except Exception as e:
        print(f"Error sending road data: {e}")

# Hàm chính
if __name__ == "__main__":
    # yêu cầu nhập đường dẫn tệp mê cung và số làn
    if len(sys.argv) < 3:
        print("Usage: python main.py <maze_file_path> <num_lanes>")
        sys.exit(1)
    maze_file_path = sys.argv[1]
    num_lanes = int(sys.argv[2])
    if not naive_create_map(maze_file_path, num_lanes):
        sys.exit(1)
    # if not create_map_from_maze_file(maze_file_path, num_lanes):
    #     sys.exit(1)
    # tạo bản đồ thành phố từ tệp bản đồ
    # if not create_map(maze_file_path, numLanes=num_lanes):
    #     sys.exit(1)

    # tạo các tuyến đường
    num_pairs = input("Số lượng cặp nút giao thông cần tạo (mặc định 20): ")
    num_pairs = int(num_pairs) if num_pairs else 20
    car_cr_type = input(f"Loại phân chia nút giao thông cho xe ({CS}, {SS}, {IO}, {OI}) (mặc định {CS}): ")
    car_cr_type = car_cr_type if car_cr_type in [CS, SS, IO, OI] else CS
    ped_option = input("Tạo tuyến đường cho người đi bộ không? (y/n, mặc định y): ")
    has_ped = ped_option.lower() != 'n'

    if has_ped:
        ped_cr_type = input(f"Loại phân chia nút giao thông cho người đi bộ ({CS}, {SS}, {IO}, {OI}) (mặc định {CS}): ")
        ped_cr_type = ped_cr_type if ped_cr_type in [CS, SS, IO, OI] else CS
        ped_impatience = input("Mức độ thiếu kiên nhẫn của người đi bộ (0.0 đến 1.0, mặc định 0.5): ")
        ped_impatience = float(ped_impatience) if ped_impatience else 0.5
        create_routes(num_pairs, car_cr_type, has_ped, ped_cr_type, ped_impatience)
    else:
        create_routes(num_pairs, car_cr_type, has_ped)


    # khởi chạy Unity và mô phỏng SUMO
    server_socket = network.create_server_socket(HOST, MAIN_PORT)
    receive_socket = network.create_server_socket("0.0.0.0", 5053)
    shutdown_socket = network.create_server_socket("0.0.0.0", 5054)

    # Khởi server thread non-daemon và lưu handle để join khi shutdown
    server_thread = async_task(network.server_thread, server_socket, client_thread_function, daemon=False)
    subprocess.Popen(target_exe)

    # Khởi các thread nền khác non-daemon để có thể shutdown gọn
    receive_thread = async_task(receive, receive_socket, daemon=False)
    listen_thread = async_task(listen_for_control_commands, shutdown_socket, daemon=False)

    try:
        # Chờ đến khi có yêu cầu dừng (được set bởi listen_for_control_commands hoặc KeyboardInterrupt)
        while not stop_event.is_set():
            time.sleep(0.5)
    except KeyboardInterrupt:
        stop_event.set()
    finally:
        # Bắt đầu đóng gọn
        for s in [server_socket, receive_socket, shutdown_socket]:
            try:
                s.close()
            except Exception:
                pass

        for t, name in ((receive_thread, 'receive'), (listen_thread, 'listen'), (server_thread, 'server')):
            try:
                if t is not None:
                    t.join(timeout=5)
            except Exception as e:
                print(f"Error joining {name} thread: {e}")

        time.sleep(0.1)


