import json
import math
import os
import socket
import subprocess
import sys
from time import sleep

import traci
import time
import threading
import network
from result import (
    VehicleTripCsvLogger,
    build_simulation_csv_path,
    build_simulation_summary_json_path,
    write_simulation_summary_json,
)

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
run_with_gui = False
has_ped = False
sim_count = 1
ped_impatience = None
maze_file_path = ""

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
            
            if msg == "Simulation end":
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
    # Our route generator writes flows using fromJunction/toJunction.
    # SUMO requires --junction-taz to treat junction IDs as valid trip endpoints.
    traci.start(["sumo", "--junction-taz", "-c", "./SUMO_xml/HelloWorld.sumocfg"])
    step_index = 0
    trip_logger = VehicleTripCsvLogger(build_simulation_csv_path("result", has_ped))
    ped_seen: set[str] = set()
    trip_logger.open()
    try:
        while traci.simulation.getMinExpectedNumber() > 0 and not stop_event.is_set():
            if pause_event.is_set():
                sleep(0.5)
                continue
            traci.simulationStep()

            # Log vehicle depart/arrival information by step.
            trip_logger.log_step(traci, step_index)
            step_index += 1
            # process_vehicle_updates(traci)
            data = {
                "trafficLights": read_traffic_lights(traci),
                "vehicles": read_vehicles(traci),
                "pedestrians": read_pedestrians(traci)
            }

            try:
                for p in data.get("pedestrians") or []:
                    ped_id = p.get("id") if isinstance(p, dict) else None
                    if ped_id:
                        ped_seen.add(str(ped_id))
            except Exception:
                # Best-effort pedestrian counting; do not break simulation.
                pass
            if run_with_gui: async_task(network.send_data, client_socket, data, join=False)
            
            current_time_step = 0.05
            with time_step_lock:
                current_time_step = time_step
            if run_with_gui: sleep(current_time_step)
    except Exception as e:
        print(f"Error during simulation: {e}")

    finally:
        # When simulation ends (naturally or by command), write summary JSON and close resources.
        from result import finish_simulation_logging
        finish_simulation_logging(trip_logger, len(ped_seen), ped_impatience, maze_file_path)
        traci.close()
        print("SUMO simulation stopped.")
        # If the simulation ended naturally, also stop the app main-loop.
        stop_event.set()

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

def parse_arguments():
    """Lấy danh sách tham số đường dẫn file mê cung và số làn đường từ command-line."""
    if len(sys.argv) < 3:
        print("Usage: python main.py <maze_file_path> <num_lanes>")
        sys.exit(1)
    
    maze_file = sys.argv[1]
    lanes = int(sys.argv[2])
    return maze_file, lanes

def setup_simulation_config():
    """Tương tác CLI với user nhằm khởi tạo thông số Traffic và GUI."""
    mode_option = input("Chạy ở chế độ nào? (1: Benchmark, 2: VRP) (mặc định 1): ")
    sim_mode = "vrp" if mode_option == "2" else "benchmark"

    config = {
        "mode": sim_mode,
    }

    if sim_mode == "benchmark":
        num_pairs_input = input("Số lượng cặp nút giao thông cần tạo (mặc định 20): ")
        config["num_pairs"] = int(num_pairs_input) if num_pairs_input else 20
        config["car_cr_type"] = input(f"Loại phân chia nút giao thông cho xe ({CS}, {SS}, {IO}, {OI}) (mặc định {CS}): ") or CS
        
        if config["car_cr_type"] not in [CS, SS, IO, OI]:
            config["car_cr_type"] = CS

        ped_option = input("Tạo tuyến đường cho người đi bộ không? (y/n, mặc định y): ")
        config["has_ped"] = ped_option.lower() != 'n'

        if config["has_ped"]:
            ped_cr_type = input(f"Loại phân chia cho người đi bộ ({CS}, {SS}, {IO}, {OI}) (mặc định {CS}): ")
            config["ped_cr_type"] = ped_cr_type if ped_cr_type in [CS, SS, IO, OI] else CS
            
            _ped_imp = input("Mức độ thiếu kiên nhẫn của người đi bộ (0.0 đến 1.0, mặc định 0.5): ")
            config["ped_impatience"] = float(_ped_imp) if _ped_imp else 0.5
        else:
            config["ped_impatience"] = None
    else:
        # VRP mode không mặc định sinh người đi bộ
        config["has_ped"] = False
        config["ped_impatience"] = None
        
        num_nodes_input = input("Số lượng điểm khách hàng (nút) cần phục vụ (mặc định 10): ")
        config["vrp_num_clients"] = int(num_nodes_input) if num_nodes_input else 10
        
        num_staff_input = input("Số lượng nhân viên giao hàng (mặc định 3): ")
        config["vrp_num_staff"] = int(num_staff_input) if num_staff_input else 3
    
    gui_option = input("Chạy với giao diện đồ họa Unity không? (y/n, mặc định n): ")
    config["run_with_gui"] = gui_option.lower() == 'y'
    
    return config

def initialize_map_and_routes(maze_file, num_lanes, config):
    """Tạo mới cấu trúc bản đồ SUMO và nạp lộ trình di chuyển."""
    if not create_map_from_maze_file(maze_file, num_lanes):
        print("[Error] Failed to create map from maze file.")
        sys.exit(1)
        
    if config["mode"] == "benchmark":
        if config["has_ped"]:
            create_routes(
                config["num_pairs"], 
                config["car_cr_type"], 
                config["has_ped"], 
                config["ped_cr_type"], 
                config["ped_impatience"]
            )
        else:
            create_routes(
                config["num_pairs"], 
                config["car_cr_type"], 
                config["has_ped"]
            )
    elif config["mode"] == "vrp":
        # Đẩy folder VRP vào sys.path để các module Python bên trong nó có thể import lẫn nhau
        # thay vì bị lỗi ModuleNotFoundError: No module named 'location'
        vrp_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "VRP")
        if vrp_path not in sys.path:
            sys.path.insert(0, vrp_path)

        from VRP.network_graph import NetworkGraph
        from VRP.company import Company
        from VRP.client import Client
        from VRP.staff import Staff
        from VRP.controller import Controller
        from VRP.xml_exporter import export_to_rou_xml
        
        print("[Info] Đang khởi tạo lộ trình VRP...")
        # VRP sử dụng .nod.xml và .edg.xml sinh ra từ create_map_from_maze_file
        node_file = "./SUMO_xml/HelloWorld.nod.xml"
        edge_file = "./SUMO_xml/HelloWorld.edg.xml"
        graph = NetworkGraph(node_file, edge_file)
        
        nodes_list = list(graph.graph.keys())
        company_node = nodes_list[0]
        start_point = Company(company_node, graph)
        
        num_requested_clients = config.get("vrp_num_clients", 10)
        # Giới hạn client nodes không vượt quá số node hiện có
        client_nodes = nodes_list[1:min(num_requested_clients + 1, len(nodes_list))]
        all_clients = [Client(node_id, graph, 10.0) for node_id in client_nodes]
        
        num_staff = config.get("vrp_num_staff", 3)
        my_staff = [Staff(i + 1, start_point) for i in range(num_staff)]
        
        assignment = Controller()
        assignment.base_case(start_point, all_clients, my_staff)
        assignment.swap_case(start_point, all_clients, my_staff)
        
        print("\n================ LỘ TRÌNH VRP DỰ KIẾN ================")
        for staff in my_staff:
            print(f"Nhân viên {staff.get_id()}:")
            print(f"  - Lộ trình (Nodes): {' -> '.join(staff.get_route())}")
            # Chi phí trên đồ thị là Thời gian di chuyển
            print(f"  - Thời gian dự kiến (s): {staff.get_total_route():.2f}")
        print("======================================================\n")

        # Ghi trực tiếp đè vào HelloWorld.rou.xml để hàm run_simulation đọc được
        output_xml = "./SUMO_xml/HelloWorld.rou.xml"
        export_to_rou_xml(my_staff, graph, output_xml)
        print("[Info] Đã tạo lộ trình VRP thành công tại", output_xml)

def start_network_services(config):
    """Khởi chạy TCP Socket Server và các background threads liên kết với Unity / SUMO."""
    server_socket = network.create_server_socket(HOST, MAIN_PORT)
    receive_socket = network.create_server_socket("0.0.0.0", 5053)
    shutdown_socket = network.create_server_socket("0.0.0.0", 5054)

    server_thread = async_task(network.server_thread, server_socket, client_thread_function, daemon=False)
    
    if config["run_with_gui"]: 
        subprocess.Popen(target_exe)
    else:
        run_simulation_thread = async_task(run_simulation, None, daemon=False)

    receive_thread = async_task(receive, receive_socket, daemon=False)
    listen_thread = async_task(listen_for_control_commands, shutdown_socket, daemon=False)
    
    return {
        "sockets": [server_socket, receive_socket, shutdown_socket],
        "threads": [
            (receive_thread, 'receive'), 
            (listen_thread, 'listen'), 
            (server_thread, 'server')
        ]
    }

def main():
    global has_ped, ped_impatience, maze_file_path, run_with_gui, time_step

    # 1. Parse command-line args
    maze_file_path, num_lanes = parse_arguments()

    # 2. Get user input / Setup configuration
    config = setup_simulation_config()
    
    # Đồng bộ biến Global cũ
    has_ped = config["has_ped"]
    ped_impatience = config["ped_impatience"]
    run_with_gui = config["run_with_gui"]
    if not run_with_gui:
        time_step = 0

    # 3. Create Simulation Map & Routes
    initialize_map_and_routes(maze_file_path, num_lanes, config)

    # 4. Start Network and Backend processes
    network_context = start_network_services(config)

    # 5. Block the main thread / Wait for termination signals
    try:
        while not stop_event.is_set():
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("Interrupted by user. Shutting down...")
        stop_event.set()
    finally:
        # 6. Cleanup Sockets and Threads
        for s in network_context["sockets"]:
            try:
                s.close()
            except Exception:
                pass

        for t, name in network_context["threads"]:
            try:
                if t is not None:
                    t.join(timeout=5)
            except Exception as e:
                print(f"Error joining {name} thread: {e}")

        time.sleep(0.1)
        print("Shutdown complete.")

if __name__ == "__main__":
    main()


