import sys
import os
import json
import traci

# Adds Server/ and Server/render/ to sys.path so all local modules resolve correctly
_render_dir = os.path.dirname(os.path.abspath(__file__))
_server_dir = os.path.dirname(_render_dir)
if _render_dir not in sys.path:
    sys.path.insert(0, _render_dir)
if _server_dir not in sys.path:
    sys.path.append(_server_dir)

from result import (
    VehicleTripCsvLogger,
    finish_simulation_logging,
)
from scenario_recorder import SimulationSession

from Traffic.trafficLight import read_traffic_lights
from Traffic.trafficer import read_trafficers
from Traffic.unity_vehicle import process_vehicle_updates
from Traffic.crossRoad import CrossRoadReader
from Traffic.edgeType0 import EdgeReader
from Traffic.crossing import CrossingReader
from osm.building import BuildingReader
from SUMO_xml.create_map_from_maze import create_map_from_maze_file
from SUMO_xml.route_gen import create_routes, create_routes_osm
from naive_map_creator import naive_create_map
# osm_to_net giữ lại cho osm_launcher.py phụ trợ; Custom Script mode không đi qua đây.
from osm.osm_to_net import convert_osm_to_net_3d_roads
from custom_script import apply_custom_script

def initialize_map_and_routes(maze_file, num_lanes, config):
    net_xml_path = "./SUMO_xml/HelloWorld.net.xml"
    # Custom Script: copy kịch bản user dựng sẵn vào SUMO_xml/ và bỏ qua sinh route.
    if config.get("custom"):
        if not apply_custom_script(maze_file):
            print("[Error] Failed to apply custom script folder.")
            sys.exit(1)
        return

    if maze_file.lower().endswith(".osm"):
        # DEPRECATED: nhánh OSM tự động không còn được launcher chính sử dụng.
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


def run_prerender(maze_file, num_lanes, config):
    print("Executing Pre-Render logic...")
    has_ped = config["has_ped"]
    ped_impatience = config.get("ped_impatience")

    initialize_map_and_routes(maze_file, num_lanes, config)

    session = SimulationSession(maze_file, has_ped=has_ped)
    print(f"Session directory: {session.session_dir}")

    # --ignore-route-errors: bỏ qua person/xe không route được thay vì quit cả mô phỏng.
    traci.start(["sumo", "--junction-taz", "--ignore-route-errors", "-c", "./SUMO_xml/HelloWorld.sumocfg"])

    step_index = 0
    trip_logger = VehicleTripCsvLogger(session.csv_path)
    ped_seen: set[str] = set()
    trip_logger.open()

    # Lưu dữ liệu bản đồ
    crossroads = CrossRoadReader.read_all_junctions()
    edges = EdgeReader.read_edges()
    crossings = CrossingReader.read_crossings()
    session.save_road_data({
        "jd": crossroads, "ed": edges, "cd": crossings,
        "bd": BuildingReader.read_buildings()  # [] nếu không phải chế độ OSM
    })
    # road_data.json đầy đủ đã lưu (pre-render headless, không gửi qua socket) → xoá cache.
    BuildingReader.discard()

    session.open()
    try:
        print("Launching SUMO simulation...")
        while traci.simulation.getMinExpectedNumber() > 0:
            traci.simulationStep()

            trip_logger.log_step(traci, step_index)
            step_index += 1
            process_vehicle_updates(traci)

            data = {
                "tl": read_traffic_lights(traci),
                "tr": read_trafficers(traci)
            }
            session.record_frame(data)

            try:
                for t in data.get("tr") or []:
                    if t.get("t") == "p":
                        ped_id = t.get("i")
                        if ped_id:
                            ped_seen.add(str(ped_id))
            except Exception:
                pass
    except KeyboardInterrupt:
        print("\n[Cảnh báo] Pre-render bị ngắt bởi người dùng. Đang lưu dữ liệu hiện tại...")
    except Exception as loop_e:
        print(f"[Lỗi] Lỗi trong quá trình mô phỏng: {loop_e}")
    finally:
        session.close()
        finish_simulation_logging(trip_logger, len(ped_seen), ped_impatience, maze_file,
                                  summary_path=session.summary_path)
        traci.close()

        print(f"SUMO simulation pre-rendering finished.")
        print(f"Total steps: {step_index}")
