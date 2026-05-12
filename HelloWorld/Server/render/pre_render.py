import sys
import os
import json
import gzip
import traci
from datetime import datetime

# Adds the Server directory to sys.path so modules can be imported correctly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from result import (
    VehicleTripCsvLogger,
    build_simulation_csv_path,
    finish_simulation_logging
)

from Traffic.trafficLight import read_traffic_lights
from Traffic.trafficer import read_trafficers
from Traffic.unity_vehicle import process_vehicle_updates
from Traffic.crossRoad import CrossRoadReader
from Traffic.edgeType0 import EdgeReader
from Traffic.crossing import CrossingReader
from SUMO_xml.create_map_from_maze import create_map_from_maze_file
from SUMO_xml.route_gen import create_routes

def initialize_map_and_routes(maze_file, num_lanes, config):
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
        node_file = "./SUMO_xml/HelloWorld.nod.xml"
        edge_file = "./SUMO_xml/HelloWorld.edg.xml"
        graph = NetworkGraph(node_file, edge_file)
        
        nodes_list = list(graph.graph.keys())
        import random
        random.shuffle(nodes_list)
        
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
    
    traci.start(["sumo", "--junction-taz", "-c", "./SUMO_xml/HelloWorld.sumocfg"])
    
    step_index = 0
    trip_logger = VehicleTripCsvLogger(build_simulation_csv_path("result", has_ped))
    ped_seen: set[str] = set()
    trip_logger.open()
    
    timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    os.makedirs("result", exist_ok=True)
    os.makedirs("map_json", exist_ok=True)
    map_base_name = os.path.splitext(os.path.basename(maze_file))[0]
    
    prerender_file_path = f"result/PreRender-{map_base_name}-{timestamp}.json.gz"
    road_data_file_path = f"map_json/RoadData-{map_base_name}-{timestamp}.json"
    
    prerender_buffer = []
    buffer_size = 0
    MAX_BUFFER_SIZE = 1024 * 1024 # 1 MB
    first_item = True

    try:
        # Lưu dữ liệu bản đồ
        crossroads = CrossRoadReader.read_all_junctions()
        edges = EdgeReader.read_edges()
        crossings = CrossingReader.read_crossings()
        road_data = {
            "jd": crossroads,
            "ed": edges,
            "cd": crossings
        }
        with open(road_data_file_path, "w", encoding="utf-8") as rdf:
            json.dump(road_data, rdf, ensure_ascii=False, separators=(',', ':'))
        print(f"Road data saved to: {road_data_file_path}")

        with gzip.open(prerender_file_path, "wt", encoding="utf-8") as out_file:
            out_file.write("[\n")
            try:
                while traci.simulation.getMinExpectedNumber() > 0:
                    traci.simulationStep()

                trip_logger.log_step(traci, step_index)
                step_index += 1
                process_vehicle_updates(traci)
                
                data = {
                    "tl": read_traffic_lights(traci),
                    "tr": read_trafficers(traci)
                }
                
                # Use compact separators to remove spaces after comma and colon
                data_str = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
                data_size = len(data_str.encode('utf-8'))
                
                prerender_buffer.append(data_str)
                buffer_size += data_size
                
                if buffer_size >= MAX_BUFFER_SIZE:
                    for item_str in prerender_buffer:
                        if not first_item:
                            out_file.write(",\n")
                        out_file.write(item_str)
                        first_item = False
                    prerender_buffer.clear()
                    buffer_size = 0

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

            # Khối này luôn được chạy dù ngắt giữa chừng, đảm bảo cấu trúc json (đóng mảng lại)
            finally:
                # Write any remaining data in the buffer
                for item_str in prerender_buffer:
                    if not first_item:
                        out_file.write(",\n")
                    out_file.write(item_str)
                    first_item = False
                out_file.write("\n]")
            
    except Exception as e:
        print(f"Error during simulation pre-rendering: {e}")
    finally:
        finish_simulation_logging(trip_logger, len(ped_seen), ped_impatience, maze_file)
        traci.close()
        
        print(f"SUMO simulation pre-rendering finished.")
        print(f"Total steps: {step_index}")
        print(f"Pre-render data saved to: {prerender_file_path}")
