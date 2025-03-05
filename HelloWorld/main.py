import traci
import json
import os
import time

OUTPUT_FILE = "./TestGR1.1/Assets/Scripts/SumoData/HelloWorld.txt"
LOCK_FILE = "./TestGR1.1/Assets/Scripts/SumoData/lock.tmp"

def run_simulation():
    traci.start(["sumo-gui", "-c", "HelloWorld.sumocfg"])

    while traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep()

        # Tạo file khóa để Unity không đọc khi Python đang ghi
        open(LOCK_FILE, "w").close()

        vehicles = []
        for veh_id in traci.vehicle.getIDList():
            vehicles.append({
                "id": veh_id,
                "position": traci.vehicle.getPosition(veh_id),
                "speed": traci.vehicle.getSpeed(veh_id),
                "lane": traci.vehicle.getLaneID(veh_id)
            })

        try:
            with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
                json.dump(vehicles, file, indent=4)
        except Exception as e:
            print(f"Lỗi khi ghi file JSON: {e}")

        # Xóa file khóa để Unity có thể đọc
        os.remove(LOCK_FILE)

        time.sleep(0.1)  # Tránh spam CPU

    traci.close()

if __name__ == "__main__":
    run_simulation()
