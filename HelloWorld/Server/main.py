import os

from render.realtime_render import run_realtime
from render.pre_render import run_prerender

CS = "CS"
SS = "SS"
IO = "IO"
OI = "OI"

def setup_simulation_config(is_custom: bool = False):
    """Tương tác CLI với user nhằm khởi tạo thông số Traffic và GUI."""
    # Custom Script: user đã dựng sẵn .sumocfg/.net.xml/.rou.xml bằng netedit
    # → bỏ qua toàn bộ prompt sinh route, chỉ hỏi GUI + render mode.
    if is_custom:
        config = {
            "mode": "custom",
            "custom": True,
            "has_ped": False,
            "ped_impatience": None,
            "session_name": input("Tên phiên (để trống = dùng tên thư mục): ").strip() or None,
        }
        render_option = input("Chế độ render? (1: Realtime, 2: Pre-render) (mặc định 1): ")
        config["render_mode"] = "pre_render" if render_option == "2" else "realtime"
        # GUI mode chỉ áp dụng cho realtime; pre-render luôn headless, chỉ ghi kịch bản.
        if config["render_mode"] == "realtime":
            gui_option = input("Chế độ hiển thị? (1: Chỉ 3D, 2: Cả 2D và 3D) (mặc định 1): ")
            config["gui_mode"] = "2d3d" if gui_option == "2" else "3d"
        _cap = input("Giới hạn số đối tượng gửi xuống Unity không? (y/n, mặc định n): ")
        if _cap.lower() == 'y':
            _max_v = input("Số xe tối đa trong cảnh (mặc định 100): ")
            config["max_vehicles_in_scene"] = int(_max_v) if _max_v else 100
            _max_p = input("Số người đi bộ tối đa trong cảnh (mặc định 100): ")
            config["max_ped_in_scene"] = int(_max_p) if _max_p else 100
        return config

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

        _car_period = input("Tần suất sinh xe (giây giữa 2 lần khởi hành, mặc định 30): ")
        config["car_period"] = float(_car_period) if _car_period else 30.0

        ped_option = input("Tạo tuyến đường cho người đi bộ không? (y/n, mặc định y): ")
        config["has_ped"] = ped_option.lower() != 'n'

        if config["has_ped"]:
            ped_cr_type = input(f"Loại phân chia cho người đi bộ ({CS}, {SS}, {IO}, {OI}) (mặc định {CS}): ")
            config["ped_cr_type"] = ped_cr_type if ped_cr_type in [CS, SS, IO, OI] else CS

            _ped_imp = input("Mức độ thiếu kiên nhẫn của người đi bộ (0.0 đến 1.0, mặc định 0.5): ")
            config["ped_impatience"] = float(_ped_imp) if _ped_imp else 0.5

            _ped_period = input("Tần suất sinh người đi bộ (giây giữa 2 lần khởi hành, mặc định 30): ")
            config["ped_period"] = float(_ped_period) if _ped_period else 30.0
        else:
            config["ped_impatience"] = None
            config["ped_period"] = 30.0

        _end_time = input("Độ dài mô phỏng — thời điểm dừng sinh agent (giây, mặc định 3600): ")
        config["end_time"] = float(_end_time) if _end_time else 3600.0

        _cap = input("Giới hạn số đối tượng gửi xuống Unity không? (y/n, mặc định n): ")
        if _cap.lower() == 'y':
            _max_v = input("Số xe tối đa trong cảnh (mặc định 100): ")
            config["max_vehicles_in_scene"] = int(_max_v) if _max_v else 100
            _max_p = input("Số người đi bộ tối đa trong cảnh (mặc định 100): ")
            config["max_ped_in_scene"] = int(_max_p) if _max_p else 100
    else:
        # VRP mode không mặc định sinh người đi bộ
        config["has_ped"] = False
        config["ped_impatience"] = None
        
        num_nodes_input = input("Số lượng điểm khách hàng (nút) cần phục vụ (mặc định 10): ")
        config["vrp_num_clients"] = int(num_nodes_input) if num_nodes_input else 10
        
        num_staff_input = input("Số lượng nhân viên giao hàng (mặc định 3): ")
        config["vrp_num_staff"] = int(num_staff_input) if num_staff_input else 3
    
    render_option = input("Chế độ render? (1: Realtime, 2: Pre-render) (mặc định 1): ")
    config["render_mode"] = "pre_render" if render_option == "2" else "realtime"

    # GUI mode chỉ áp dụng cho realtime; pre-render luôn headless, chỉ ghi kịch bản.
    if config["render_mode"] == "realtime":
        gui_option = input("Chế độ hiển thị? (1: Chỉ 3D, 2: Cả 2D và 3D) (mặc định 1): ")
        config["gui_mode"] = "2d3d" if gui_option == "2" else "3d"

    return config

def main():
    # 1. Đọc maze_file và num_lanes từ stdin (launcher gửi trước khi gửi config)
    maze_file_path = input().strip()
    num_lanes = int(input().strip())

    # 2. Detect Custom Script mode: launcher truyền 1 thư mục chứa kịch bản
    # do user dựng sẵn bằng netedit thay vì 1 file .map.
    is_custom = os.path.isdir(maze_file_path)

    # 3. Get user input / Setup configuration
    config = setup_simulation_config(is_custom=is_custom)

    # 4. Route to logic
    if config.get("render_mode") == "pre_render":
        run_prerender(maze_file_path, num_lanes, config)
    else:
        run_realtime(maze_file_path, num_lanes, config)

if __name__ == "__main__":
    main()


