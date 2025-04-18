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
def async_task(target, *args):
    thread = threading.Thread(target=target, args=args)
    thread.daemon = True  # Tự động dừng khi main kết thúc
    thread.start()

# Hàm chạy mô phỏng SUMO và ghi dữ liệu
def run_simulation():
    traci.start(["sumo-gui", "-c", "HelloWorld.sumocfg"])
    try:
        while traci.simulation.getMinExpectedNumber() > 0:
            traci.simulationStep()

            process_vehicle_updates(traci)  # ✅ Xử lý cập nhật xe tại đây

            read_and_send_traffic_lights(traci)
            read_and_send_vehicles(traci)
            read_and_send_pedestrians(traci)
            time.sleep(1 / 60)

    finally:
        traci.close()


# Hàm chính
if __name__ == "__main__":
    #subprocess.Popen(target_exe)
    async_task(receive)
    CrossRoadReader.read_all_junctions()
    EdgeReader.read_edges()
    CrossingReader.read_crossings()
    print("Starting simulation...")
    run_simulation()
    print("Simulation completed!")



