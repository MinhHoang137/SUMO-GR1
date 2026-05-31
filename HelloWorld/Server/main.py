import sys
import os

from render.realtime_render import run_realtime
from render.pre_render import run_prerender

CS = "CS"
SS = "SS"
IO = "IO"
OI = "OI"

def parse_arguments():
    """Lấy danh sách tham số đường dẫn file mê cung và số làn đường từ command-line."""
    if len(sys.argv) < 3:
        print("Usage: python main.py <maze_file_path> <num_lanes>")
        sys.exit(1)
    
    maze_file = sys.argv[1]
    lanes = int(sys.argv[2])
    return maze_file, lanes

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
        }
        gui_option = input("Chạy với giao diện đồ họa Unity không? (y/n, mặc định n): ")
        config["run_with_gui"] = gui_option.lower() == 'y'
        render_option = input("Chế độ render? (1: Realtime, 2: Pre-render) (mặc định 1): ")
        config["render_mode"] = "pre_render" if render_option == "2" else "realtime"
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

        ped_option = input("Tạo tuyến đường cho người đi bộ không? (y/n, mặc định y): ")
        config["has_ped"] = ped_option.lower() != 'n'

        if config["has_ped"]:
            ped_cr_type = input(f"Loại phân chia cho người đi bộ ({CS}, {SS}, {IO}, {OI}) (mặc định {CS}): ")
            config["ped_cr_type"] = ped_cr_type if ped_cr_type in [CS, SS, IO, OI] else CS
            
            _ped_imp = input("Mức độ thiếu kiên nhẫn của người đi bộ (0.0 đến 1.0, mặc định 0.5): ")
            config["ped_impatience"] = float(_ped_imp) if _ped_imp else 0.5
        else:
            config["ped_impatience"] = None
    else:
        # VRP mode không mặc định sinh người đi bộ
        config["has_ped"] = False
        config["ped_impatience"] = None
        
        num_nodes_input = input("Số lượng điểm khách hàng (nút) cần phục vụ (mặc định 10): ")
        config["vrp_num_clients"] = int(num_nodes_input) if num_nodes_input else 10
        
        num_staff_input = input("Số lượng nhân viên giao hàng (mặc định 3): ")
        config["vrp_num_staff"] = int(num_staff_input) if num_staff_input else 3
    
    gui_option = input("Chạy với giao diện đồ họa Unity không? (y/n, mặc định n): ")
    config["run_with_gui"] = gui_option.lower() == 'y'
    
    render_option = input("Chế độ render? (1: Realtime, 2: Pre-render) (mặc định 1): ")
    config["render_mode"] = "pre_render" if render_option == "2" else "realtime"

    return config

def main():
    # 1. Parse command-line args
    maze_file_path, num_lanes = parse_arguments()

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


