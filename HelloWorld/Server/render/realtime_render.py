import sys
import os

# Adds Server/ and Server/render/ to sys.path so all local modules resolve correctly
_render_dir = os.path.dirname(os.path.abspath(__file__))
_server_dir = os.path.dirname(_render_dir)
if _render_dir not in sys.path:
    sys.path.insert(0, _render_dir)
if _server_dir not in sys.path:
    sys.path.append(_server_dir)

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
    finish_simulation_logging,
)
from scenario_recorder import SimulationSession

from Traffic.crossing import CrossingReader
from Traffic.crossRoad import CrossRoadReader
from Traffic.edgeType0 import EdgeReader
from Traffic.trafficLight import read_traffic_lights
from Traffic.trafficer import read_trafficers
from Traffic.unity_vehicle import receive, process_vehicle_updates
from osm.building import BuildingReader
from SUMO_xml.create_map_from_maze import create_map_from_maze_file
from SUMO_xml.route_gen import create_routes, create_routes_osm
from SUMO_xml.create_city_map import create_map
from naive_map_creator import naive_create_map
# osm_to_net: đường dẫn .osm→.net.xml CŨ, chỉ còn osm_launcher.py / debug tay dùng.
# Luồng OSM chính hiện nay đi qua osm.build_scenario (sinh sẵn net+rou+cfg vào SUMO_xml/),
# rồi nạp lại bằng apply_custom_script (xem custom_script.py để hiểu vai trò loader này).
from osm.osm_to_net import convert_osm_to_net_3d_roads
from custom_script import apply_custom_script

CS = "CS"
SS = "SS"
IO = "IO"
OI = "OI"

MAX_PACKET_SIZE = 131072 # 128 KB
MAX_RETRIES = 5
END_MARKER = '<END>'

target_exe = "../../UnityBuild/TestGR1.1.exe"  # tương đối từ Server/render/ → HelloWorld/UnityBuild/
stop_event = threading.Event()
time_step = 0.05  # Giãn cách thời gian thực (giây) giữa các simulationStep khi chạy GUI. Khởi tạo từ launcher, Unity chỉnh được lúc chạy.
time_step_lock = threading.Lock()
# Pause/resume simulation (thread-safe). Unity should control this via commands.
pause_event = threading.Event()  # set => paused, clear => running
show_sumo_gui = False  # True => mở thêm cửa sổ sumo-gui (2D) song song Unity (3D); False => chỉ 3D
has_ped = False
sim_count = 1
ped_impatience = None
maze_file_path = ""
simulation_session: SimulationSession | None = None
max_vehicles_in_scene: int | None = None  # None = không giới hạn
max_ped_in_scene: int | None = None

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
                        val = float(data["timeStep"])  # Unity gửi mili-giây
                        if val > 0:
                            with time_step_lock:
                                global time_step
                                time_step = val / 1000.0
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
    print("Launching SUMO simulation...")
    # --ignore-route-errors: nếu còn person/xe nào không route được (vd vỉa hè cụm junction
    # bị ngắt), SUMO bỏ qua thay vì quit cả mô phỏng. Net-an-toàn lúc demo hội đồng.
    sumo_binary = "sumo-gui" if show_sumo_gui else "sumo"
    traci.start([sumo_binary, "--junction-taz", "--ignore-route-errors", "-c", "./SUMO_xml/HelloWorld.sumocfg"])
    print(f"[MONITOR] TIME_STEP: {time_step}", flush=True)
    step_index = 0
    trip_logger = VehicleTripCsvLogger(simulation_session.csv_path if simulation_session else "result/trips.csv")
    ped_seen: set[str] = set()
    trip_logger.open()
    if simulation_session:
        simulation_session.open()
    try:
        while traci.simulation.getMinExpectedNumber() > 0 and not stop_event.is_set():
            if pause_event.is_set():
                sleep(0.5)
                continue
            loop_start = time.perf_counter()  # mốc đo a = thời gian xử lý 1 vòng lặp
            traci.simulationStep()

            trip_logger.log_step(traci, step_index)
            step_index += 1
            process_vehicle_updates(traci)
            tr = read_trafficers(traci)
            if max_vehicles_in_scene is not None or max_ped_in_scene is not None:
                cars = [t for t in tr if t.get("t") != "p"]
                peds = [t for t in tr if t.get("t") == "p"]
                if max_vehicles_in_scene is not None:
                    cars = cars[:max_vehicles_in_scene]
                if max_ped_in_scene is not None:
                    peds = peds[:max_ped_in_scene]
                tr = cars + peds
            data = {
                "st": step_index,  # bước SUMO hiện tại — client dùng để đếm vòng đời xác xe (wreck)
                "tl": read_traffic_lights(traci),
                "tr": tr
            }

            try:
                for t in data.get("tr") or []:
                    if t.get("t") == "p":
                        ped_id = t.get("i")
                        if ped_id:
                            ped_seen.add(str(ped_id))
            except Exception:
                pass

            if simulation_session:
                simulation_session.record_frame(data)

            # Đính timestamp gửi (epoch mili-giây) ngay sát lúc stream để Unity đo độ trễ
            # end-to-end. Đặt SAU record_frame nên session/replay không lưu "ts" (không cần).
            data["ts"] = int(time.time() * 1000)
            # Realtime luôn có Unity là client → luôn stream và giãn nhịp.
            # Nén luồng stream (raw-deflate+base64) để giảm băng thông/parse phía Unity.
            network.send_data(client_socket, data, compress=network.COMPRESS_DOWNLOAD)

            with time_step_lock:
                current_time_step = time_step
            # a = thời gian đã trôi của vòng lặp; b = phần còn lại để a + b = time_step.
            elapsed = time.perf_counter() - loop_start
            remaining = current_time_step - elapsed
            if remaining > 0:
                sleep(remaining)
    except Exception as e:
        print(f"Error during simulation: {e}")
    finally:
        if simulation_session:
            simulation_session.close()
        finish_simulation_logging(
            trip_logger, len(ped_seen), ped_impatience, maze_file_path,
            summary_path=simulation_session.summary_path if simulation_session else None,
        )
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
        "cd": crossings,
        "bd": BuildingReader.read_buildings()  # [] nếu không phải chế độ OSM
    }
    if simulation_session:
        simulation_session.save_road_data(road_data)
    try:
        for i in range(MAX_RETRIES):
            if not network.send_data(client_socket, road_data):
                print("Retrying to send road data...")
                time.sleep(1)
            else:
                break
        print("Road data sent successfully.")
        # road_data.json đầy đủ đã được lưu + gửi → xoá cache building trung gian.
        BuildingReader.discard()
    except Exception as e:
        print(f"Error sending road data: {e}")

def initialize_map_and_routes(maze_file, num_lanes, config):
    net_xml_path = "./SUMO_xml/HelloWorld.net.xml"
    # Nạp kịch bản dựng-sẵn từ một thư mục (config["custom"], bật khi maze_file là dir):
    # luồng OSM auto-gen đã sinh net/rou/cfg vào SUMO_xml/ → chỉ chốt lại bộ file và bỏ
    # qua sinh route tự động. (Không phải mode người dùng tự dựng — xem custom_script.py.)
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
        # Benchmark: sinh mạng theo kiểu vét cạn (mỗi ô '.' là một node) để tạo mạng dày,
        # đúng tinh thần đo tải hệ thống. KHÔNG dùng create_map_from_maze_file (sinh mạng
        # thưa, tối ưu node) cho tệp .map nữa.
        if not naive_create_map(maze_file, num_lanes):
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
                    edge_file_path=_edge_file,
                    car_period=config.get("car_period", 30.0),
                    ped_period=config.get("ped_period", 30.0),
                    end_time=config.get("end_time", 3600.0),
                )
            else:
                create_routes(
                    config["num_pairs"],
                    config["car_cr_type"],
                    config["has_ped"],
                    edge_file_path=_edge_file,
                    car_period=config.get("car_period", 30.0),
                    end_time=config.get("end_time", 3600.0),
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
        # DEPRECATED: nhánh nhận .osm trực tiếp này chỉ còn cho main.py legacy/debug tay.
        # Luồng OSM chính giờ sinh sẵn file qua build_scenario rồi nạp dạng thư mục
        # (config["custom"]), nên maze_file ở đây hiếm khi còn là .osm.
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
    
    # Realtime luôn khởi chạy Unity (3D). Chế độ headless đã được thay bằng pre-render.
    subprocess.Popen([os.path.abspath(os.path.join(os.path.dirname(__file__), target_exe))])

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
    global has_ped, ped_impatience, maze_file_path, show_sumo_gui, simulation_session, max_vehicles_in_scene, max_ped_in_scene

    maze_file_path = maze_file
    has_ped = config["has_ped"]
    ped_impatience = config["ped_impatience"]
    show_sumo_gui = config.get("gui_mode") == "2d3d"  # mặc định chỉ 3D
    max_vehicles_in_scene = config.get("max_vehicles_in_scene")
    max_ped_in_scene = config.get("max_ped_in_scene")

    initialize_map_and_routes(maze_file_path, num_lanes, config)

    session_name = config.get("session_name") or maze_file_path
    simulation_session = SimulationSession(session_name, has_ped=has_ped)
    print(f"Session directory: {simulation_session.session_dir}")

    # Lưu road data ngay sau khi map được tạo để session luôn đầy đủ
    # (Unity cũng sẽ yêu cầu road data qua RoadDataRequest khi kết nối).
    crossroads = CrossRoadReader.read_all_junctions()
    edges = EdgeReader.read_edges()
    crossings = CrossingReader.read_crossings()
    # Đọc building không huỷ cache ở đây — send_road_data (khi Unity kết nối) cần đọc lại
    # rồi mới discard.
    simulation_session.save_road_data({
        "jd": crossroads, "ed": edges, "cd": crossings,
        "bd": BuildingReader.read_buildings()
    })

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
