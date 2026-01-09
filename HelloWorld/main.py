import json
import math
import socket
import subprocess
import sys
from time import sleep
from queue import Queue, Full, Empty

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
import Traffic.unity_vehicle as unity_vehicle
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
# How often we send state to Unity (every N simulation steps).
send_every_n_steps = 1
send_every_n_steps_lock = threading.Lock()

# Lightweight profiler: print averages every N steps (0 disables).
profile_every_n_steps = 10
profile_every_n_steps_lock = threading.Lock()
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
        "sendEvery": ("send_every_n_steps", send_every_n_steps_lock),
        "profileEvery": ("profile_every_n_steps", profile_every_n_steps_lock),
    }

    # Unity vehicle update knobs (reduce TraCI calls)
    if "unityEvery" in data:
        try:
            unity_vehicle.set_apply_every(int(float(data["unityEvery"])))
        except Exception:
            pass
    if "applySpeed" in data:
        try:
            unity_vehicle.set_apply_speed(bool(int(float(data["applySpeed"]))))
        except Exception:
            pass
    if "applySignals" in data:
        try:
            unity_vehicle.set_apply_signals(bool(int(float(data["applySignals"]))))
        except Exception:
            pass

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
                    # Centralized update supports: timeStep(ms), sendEvery(steps), profileEvery(steps)
                    process_config_update(data)
                    if "timeStep" in data:
                        # Convert ms to seconds; allow 0 to mean "no sleep".
                        try:
                            val_ms = float(data["timeStep"])
                            if val_ms >= 0:
                                with time_step_lock:
                                    global time_step
                                    time_step = val_ms / 1000.0
                        except Exception:
                            pass
                except Exception as e:
                    print(f"[Error] Failed to process JSON config: {e}")
            else:
                # Giữ lại như 1 cảnh báo vì có thể là lỗi protocol
                print(f"[Warn] Unknown command from Unity: {msg}")
            
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

    # Single sender thread to avoid concurrent writes to the same socket.
    send_queue: Queue = Queue(maxsize=1)  # keep newest only
    sender_stop = threading.Event()

    def _sender_loop() -> None:
        while not sender_stop.is_set() and not stop_event.is_set():
            try:
                payload = send_queue.get(timeout=0.25)
            except Empty:
                continue
            if payload is None:
                break
            try:
                network.send_data(client_socket, payload)
            except Exception as e:
                print(f"Error sending simulation data: {e}")
                break

    sender_thread = async_task(_sender_loop, daemon=True)

    step_idx = 0
    # Profiling accumulators (seconds)
    acc_sim = acc_unity = acc_read = acc_sendq = acc_sleep = 0.0
    try:
        while traci.simulation.getMinExpectedNumber() > 0 and not stop_event.is_set():
            if pause_event.is_set():
                sleep(0.5)
                continue

            t0 = time.perf_counter()
            traci.simulationStep()
            t1 = time.perf_counter()
            process_vehicle_updates(traci)
            t2 = time.perf_counter()

            do_send = True
            with send_every_n_steps_lock:
                n = int(send_every_n_steps) if int(send_every_n_steps) > 0 else 1
            if (step_idx % n) != 0:
                do_send = False

            if do_send:
                # Reading TraCI state is usually the hottest part. Only do it when we actually send.
                data = {
                    "trafficLights": read_traffic_lights(traci),
                    "vehicles": read_vehicles(traci),
                    "pedestrians": read_pedestrians(traci)
                }
                # Serialize once here so sender thread only does socket I/O.
                payload = json.dumps(data, separators=(",", ":"))
                t3 = time.perf_counter()
                try:
                    send_queue.put_nowait(payload)
                except Full:
                    try:
                        _ = send_queue.get_nowait()
                    except Exception:
                        pass
                    try:
                        send_queue.put_nowait(payload)
                    except Exception:
                        pass
                t4 = time.perf_counter()
            else:
                t3 = t4 = time.perf_counter()
            
            current_time_step = 0.05
            with time_step_lock:
                current_time_step = time_step

            t5 = time.perf_counter()
            if current_time_step > 0:
                sleep(current_time_step)
            t6 = time.perf_counter()

            # Update profiling accumulators
            acc_sim += (t1 - t0)
            acc_unity += (t2 - t1)
            acc_read += (t3 - t2)
            acc_sendq += (t4 - t3)
            acc_sleep += (t6 - t5)

            step_idx += 1

            with profile_every_n_steps_lock:
                prof_n = int(profile_every_n_steps)
            if prof_n > 0 and (step_idx % prof_n) == 0:
                denom = float(prof_n)
                avg_sim = (acc_sim / denom) * 1000.0
                avg_unity = (acc_unity / denom) * 1000.0
                avg_read = (acc_read / denom) * 1000.0
                avg_sendq = (acc_sendq / denom) * 1000.0
                avg_sleep = (acc_sleep / denom) * 1000.0
                avg_total = avg_sim + avg_unity + avg_read + avg_sendq + avg_sleep
                print(
                    f"[Perf] avg/step ms: total={avg_total:.2f} | simStep={avg_sim:.2f} | "
                    f"unityUpdate={avg_unity:.2f} | read+json={avg_read:.2f} | enqueue={avg_sendq:.2f} | sleep={avg_sleep:.2f}"
                )
                acc_sim = acc_unity = acc_read = acc_sendq = acc_sleep = 0.0

    finally:
        sender_stop.set()
        try:
            send_queue.put_nowait(None)
        except Exception:
            pass
        try:
            if sender_thread is not None:
                sender_thread.join(timeout=2)
        except Exception:
            pass
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


