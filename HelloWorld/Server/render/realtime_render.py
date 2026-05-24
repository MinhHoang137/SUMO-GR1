import sys
import os

# Adds the Server directory to sys.path so modules can be imported correctly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import math
import socket
import subprocess
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
from Traffic.trafficer import read_trafficers
from Traffic.unity_vehicle import receive, process_vehicle_updates
from SUMO_xml.create_map_from_maze import create_map_from_maze_file
from SUMO_xml.route_gen import create_routes, create_routes_osm
from SUMO_xml.create_city_map import create_map
from naive_map_creator import naive_create_map
# osm_to_net giữ lại cho osm_launcher.py phụ trợ (tạo .net.xml 3D từ .osm). Custom Script
# mode không dùng đường dẫn này — user tự dựng kịch bản trong netedit.
from osm_to_net import convert_osm_to_net_3d_roads
from custom_script import apply_custom_script

CS = "CS"
SS = "SS"
IO = "IO"
OI = "OI"

MAX_PACKET_SIZE = 131072 # 128 KB
MAX_RETRIES = 5
END_MARKER = '<END>'

target_exe = "../UnityBuild/TestGR1.1.exe"
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
    thread.daemon = daemon
    thread.start()
    if join:
        thread.join()
    return thread

def process_config_update(data: dict):
    param_map = {
        "timeStep": ("time_step", time_step_lock),
    }

    for key, value in data.items():
        if key in param_map:
            var_name, lock = param_map[key]
            try:
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
    print("[MONITOR] CLIENT_CONNECTED", flush=True)
    if "RoadDataRequest" in first_msg:
        send_road_data(socket)
        socket.close()
    if ("SimulationReady" in first_msg):
        print("Starting simulation...")
        print("[MONITOR] STATE: PLAYING", flush=True)
        run_simulation(client_socket=socket)
        print("Simulation completed!")
        print("[MONITOR] STATE: STOPPED", flush=True)
    return 0

def cmd_handler(client_socket: socket.socket):
    try:
        while True:
            try:
                msg = network.receive_message(client_socket)
            except socket.timeout:
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
                print("Client disconnected from simulation command listener.")
                stop_event.set()
                break
            elif msg == "Pause":
                set_pause_sim(True)
                print("Simulation paused.")
                print("[MONITOR] STATE: PAUSED", flush=True)
            elif msg == "Resume":
                set_pause_sim(False)
                print("Simulation resumed.")
                print("[MONITOR] STATE: PLAYING", flush=True)
            elif msg.startswith("{") and msg.endswith("}"):
                try:
                    data = json.loads(msg)
                    if "timeStep" in data:
                        val = float(data["timeStep"])
                        if val > 0:
                            with time_step_lock:
                                global time_step
                                time_step = val/1000.0
                            print(f"[Info] Updated time_step to {time_step}")
                            print(f"[MONITOR] TIME_STEP: {time_step}", flush=True)
                except Exception as e:
                    print(f"[Error] Failed to process JSON config: {e}")
            else:
                print(f"[Info] Unknown command from Unity: {msg}")
            
            time.sleep(0.01)

    except Exception as e:
        print(f"Error in command handler: {e}")
    finally:
        client_socket.close()

def listen_for_control_commands(cmd_socket):
    network.server_thread(cmd_socket, cmd_handler)
    return 0

def run_simulation(client_socket: socket.socket):
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

            trip_logger.log_step(traci, step_index)
            step_index += 1
            process_vehicle_updates(traci)
            data = {
                "tl": read_traffic_lights(traci),
                "tr": read_trafficers(traci)
            }

            try:
                for t in data.get("tr") or []:
                    if t.get("t") == "p":
                        ped_id = t.get("i")
                        if ped_id:
                            ped_seen.add(str(ped_id))
            except Exception:
                pass
            
            if run_with_gui: 
                network.send_data(client_socket, data)
            
            current_time_step = 0.05
            with time_step_lock:
                current_time_step = time_step
            if run_with_gui: sleep(current_time_step)
    except Exception as e:
        print(f"Error during simulation: {e}")
    finally:
        from result import finish_simulation_logging
        finish_simulation_logging(trip_logger, len(ped_seen), ped_impatience, maze_file_path)
        traci.close()
        print("SUMO simulation stopped.")
        stop_event.set()

def send_road_data(client_socket: socket.socket):
    crossroads = CrossRoadReader.read_all_junctions()
    edges =  EdgeReader.read_edges()
    crossings = CrossingReader.read_crossings()
    road_data = {
        "jd": crossroads,
        "ed": edges,
        "cd": crossings
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

def initialize_map_and_routes(maze_file, num_lanes, config):
    net_xml_path = "./SUMO_xml/HelloWorld.net.xml"
    # Custom Script: user đã dựng .sumocfg/.net.xml/.rou.xml bằng netedit
    # → chỉ copy vào SUMO_xml/ và bỏ qua toàn bộ sinh route tự động.
    if config.get("custom"):
        if not apply_custom_script(maze_file):
            print("[Error] Failed to apply custom script folder.")
            sys.exit(1)
        return

    if maze_file.lower().endswith(".osm"):
        # DEPRECATED: nhánh OSM tự động không còn được launcher chính sử dụng.
        # Giữ lại để osm_launcher.py / debug tay có thể tận dụng pipeline cũ.
        osm_output = net_xml_path
        if not convert_osm_to_net_3d_roads(maze_file, osm_output):
            print("[Error] Failed to convert OSM file to SUMO network.")
            sys.exit(1)
    else:
        if not create_map_from_maze_file(maze_file, num_lanes):
            print("[Error] Failed to create map from maze file.")
            sys.exit(1)

    if config["mode"] == "benchmark":
        # DEPRECATED: nhánh OSM benchmark không còn đi qua launcher chính.
        # Launcher hiện chỉ ghép Benchmark với .map; nhánh dưới chỉ chạy khi
        # gọi main.py trực tiếp với tham số .osm (debug/legacy).
        if maze_file.lower().endswith(".osm"):
            # OSM mode: dùng explicit Dijkstra routes thay vì TAZ routing
            create_routes_osm(
                config["num_pairs"],
                config["car_cr_type"],
                config["has_ped"],
                config.get("ped_cr_type", "CS"),
                config.get("ped_impatience", 0.5),
                net_xml_path=net_xml_path
            )
        else:
            # Maze mode: dùng TAZ routing (fromJunction/toJunction)
            _edge_file = None
            if config["has_ped"]:
                create_routes(
                    config["num_pairs"],
                    config["car_cr_type"],
                    config["has_ped"],
                    config["ped_cr_type"],
                    config["ped_impatience"],
                    edge_file_path=_edge_file
                )
            else:
                create_routes(
                    config["num_pairs"],
                    config["car_cr_type"],
                    config["has_ped"],
                    edge_file_path=_edge_file
                )
    elif config["mode"] == "vrp":
        vrp_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "VRP")
        if vrp_path not in sys.path:
            sys.path.insert(0, vrp_path)

        from VRP.network_graph import NetworkGraph
        from VRP.company import Company
        from VRP.client import Client
        from VRP.staff import Staff
        from VRP.controller import Controller
        from VRP.xml_exporter import export_to_rou_xml
        
        print("[Info] Đang khởi tạo lộ trình VRP...")
        net_xml_path = "./SUMO_xml/HelloWorld.net.xml"
        # DEPRECATED: nhánh OSM VRP không còn đi qua launcher chính (OSM đã được
        # thay bằng Custom Script). Giữ lại để main.py legacy với .osm vẫn chạy.
        if maze_file.lower().endswith(".osm"):
            # OSM path: chỉ có .net.xml, đọc trực tiếp từ đó
            graph = NetworkGraph.from_net_xml(net_xml_path)
        else:
            # Maze path: đọc từ .nod.xml và .edg.xml riêng biệt
            node_file = "./SUMO_xml/HelloWorld.nod.xml"
            edge_file = "./SUMO_xml/HelloWorld.edg.xml"
            graph = NetworkGraph(node_file, edge_file)
        
        # Chỉ giữ các node có đường đi ra (loại bỏ node cô lập)
        nodes_list = [n for n in graph.graph if graph.graph[n]]
        import random
        random.shuffle(nodes_list)
        
        if not nodes_list:
            print("[Error] Không tìm thấy node hợp lệ trong mạng lưới.")
            sys.exit(1)
        
        company_node = nodes_list[0]
        start_point = Company(company_node, graph)
        
        num_requested_clients = config.get("vrp_num_clients", 10)
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
            print(f"  - Thời gian dự kiến (s): {staff.get_total_route():.2f}")
        print("======================================================\n")

        output_xml = "./SUMO_xml/HelloWorld.rou.xml"
        export_to_rou_xml(my_staff, graph, output_xml)
        print("[Info] Đã tạo lộ trình VRP thành công tại", output_xml)

def start_network_services(config):
    server_socket = network.create_server_socket(HOST, MAIN_PORT)
    receive_socket = network.create_server_socket(HOST, 5053)
    cmd_socket = network.create_server_socket(HOST, 5054)

    server_thread = async_task(network.server_thread, server_socket, client_thread_function, daemon=False)
    
    if config["run_with_gui"]: 
        pass
    else:
        run_simulation_thread = async_task(run_simulation, None, daemon=False)

    receive_thread = async_task(receive, receive_socket, daemon=False)
    listen_thread = async_task(listen_for_control_commands, cmd_socket, daemon=False)
    
    return {
        "sockets": [server_socket, receive_socket, cmd_socket],
        "threads": [
            (receive_thread, 'receive'), 
            (listen_thread, 'listen'), 
            (server_thread, 'server')
        ]
    }

def run_realtime(maze_file, num_lanes, config):
    global has_ped, ped_impatience, maze_file_path, run_with_gui, time_step

    maze_file_path = maze_file
    has_ped = config["has_ped"]
    ped_impatience = config["ped_impatience"]
    run_with_gui = config["run_with_gui"]
    if not run_with_gui:
        time_step = 0

    initialize_map_and_routes(maze_file_path, num_lanes, config)
    network_context = start_network_services(config)

    try:
        while not stop_event.is_set():
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("Interrupted by user. Shutting down...")
        stop_event.set()
    finally:
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
        os._exit(0)
