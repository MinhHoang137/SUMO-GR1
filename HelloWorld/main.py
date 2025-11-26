import json
import math
import socket
import subprocess
import sys
from time import sleep

import traci
import time
import threading
from Traffic.crossing import CrossingReader
from Traffic.crossRoad import CrossRoadReader
from Traffic.edgeType0 import EdgeReader
from Traffic.trafficLight import read_traffic_lights
from Traffic.vehicle import read_vehicles
from Traffic.pedestrian import read_pedestrians
from Traffic.unity_vehicle import receive, process_vehicle_updates
from SUMO_xml.create_map_from_maze import create_map_from_maze_file
from SUMO_xml.route_gen import create_routes

CS = "CS"
SS = "SS"
IO = "IO"
OI = "OI"

MAX_PACKET_SIZE = 100000
MAX_RETRIES = 5
target_exe = "./UnityBuild/TestGR1.1.exe"
stop_event = threading.Event()
time_step = 0.11  # Giả sử mỗi bước mô phỏng là 0.11 giây

def async_task(target, *args):
    thread = threading.Thread(target=target, args=args)
    thread.daemon = True  # Tự động dừng khi main kết thúc
    thread.start()

# Nhận lệnh từ Unity để dừng mô phỏng
def listen_for_shutdown_command():
    host = "127.0.0.1"
    port = 5054
    buffer_size = 1024
    expected_msg = "Simulation end"
    print("Listening for shutdown command on port 5054...")
    while not stop_event.is_set():
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
                server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                server.bind((host, port))
                server.listen(1)
                server.settimeout(3.0)  # Timeout để thử lại liên tục

                # print("Listening for shutdown command on port 5054...")
                conn, addr = server.accept()
                with conn:
                    data = b""
                    while True:
                        chunk = conn.recv(buffer_size)
                        if not chunk:
                            break
                        data += chunk
                        if b"<END>" in data:
                            break

                    message = data.decode("utf-8").replace("<END>", "").strip()
                    print(f"Received message: {message}")
                    if expected_msg in message:
                        stop_event.set()
                        break
        except socket.timeout:
            continue
        except Exception as e:
            print(f"[Error] Socket exception: {e}")
            time.sleep(1)

# Hàm chạy mô phỏng SUMO và ghi dữ liệu
def run_simulation():
    traci.start(["sumo-gui", "-c", "./SUMO_xml/HelloWorld.sumocfg"])
    try:
        while traci.simulation.getMinExpectedNumber() > 0 and not stop_event.is_set():
            traci.simulationStep()
            # for person_id in traci.person.getIDList():
            #     print(f"type: {traci.person.getTypeID(person_id)}, impatient: {traci.person.getImpatience(person_id)}")
            process_vehicle_updates(traci)
            data = {
                "trafficLights": read_traffic_lights(traci),
                "vehicles": read_vehicles(traci),
                "pedestrians": read_pedestrians(traci)
            }
            send(data)
            sleep(time_step)

    finally:
        traci.close()
        print("SUMO simulation stopped.")

def send(data, host='127.0.0.1', port=5050):
    """Nhận danh sách dict, chuyển thành JSON string và gửi đi"""
    try:
        data_str = json.dumps(data)
        total_size = len(data_str)
        num_packets = math.ceil(total_size / MAX_PACKET_SIZE)

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((host, port))

            print(f"Sending {num_packets} packets...")

            # Gửi từng gói dữ liệu
            for i in range(num_packets):
                start = i * MAX_PACKET_SIZE
                end = min(start + MAX_PACKET_SIZE, total_size)
                packet = data_str[start:end]
                s.sendall(packet.encode('utf-8'))

            # Gửi thông báo kết thúc
            s.sendall(b"<END>")

            # Nhận phản hồi từ Unity (nếu cần)
            response = s.recv(1024)
            print(f"Response from Unity: {response.decode('utf-8')}")
            return True

    except Exception as e:
        print(f"Error sending data: {e}")
        return False

def send_road_data():
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
            if not send(road_data):
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
    if not create_map_from_maze_file(maze_file_path, num_lanes):
        sys.exit(1)
        

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
    subprocess.Popen(target_exe)
    async_task(receive)
    async_task(listen_for_shutdown_command)

    send_road_data()

    print("Starting simulation...")
    run_simulation()
    print("Simulation completed!")
