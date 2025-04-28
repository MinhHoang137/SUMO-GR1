import socket
import subprocess
import traci
import time
import threading
from crossing import CrossingReader
from crossRoad import CrossRoadReader
from edgeType0 import EdgeReader
from trafficLight import read_and_send_traffic_lights
from vehicle import read_and_send_vehicles
from pedestrian import read_and_send_pedestrians
from unity_vehicle import receive, process_vehicle_updates

target_exe = "./UnityBuild/TestGR1.1.exe"
stop_event = threading.Event()

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
    traci.start(["sumo-gui", "-c", "HelloWorld.sumocfg"])
    try:
        while traci.simulation.getMinExpectedNumber() > 0 and not stop_event.is_set():
            traci.simulationStep()
            process_vehicle_updates(traci)
            read_and_send_traffic_lights(traci)
            read_and_send_vehicles(traci)
            read_and_send_pedestrians(traci)
    finally:
        traci.close()
        print("SUMO simulation stopped.")

# Hàm chính
if __name__ == "__main__":
    subprocess.Popen(target_exe)
    async_task(receive)
    async_task(listen_for_shutdown_command)

    CrossRoadReader.read_all_junctions()
    EdgeReader.read_edges()
    CrossingReader.read_crossings()

    print("Starting simulation...")
    run_simulation()
    print("Simulation completed!")
