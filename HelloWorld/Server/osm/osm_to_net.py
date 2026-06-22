

import os
import argparse
import subprocess

def convert_osm_to_net_3d_roads(osm_file, output_net_file=None, mode="3d"):
    """Chuyển .osm → .net.xml qua netconvert.

    Args:
        mode: "2d" (phẳng — khuyến khích cho bản đồ không có cầu vượt chồng chéo)
              hoặc "3d" (giữ cao độ từ OSM + nâng layer cho cầu vượt).
    """
    if not os.path.exists(osm_file):
        print(f"[Lỗi] Không tìm thấy tệp đầu vào (OSM): {osm_file}")
        return False

    if output_net_file is None:
        # Nếu không truyền tên file đầu ra, tự động lấy tên file osm thêm đuôi .net.xml
        output_net_file = os.path.splitext(osm_file)[0] + ".net.xml"

    mode = (mode or "2d").lower()
    if mode not in ("2d", "3d"):
        print(f"[Cảnh báo] mode='{mode}' không hợp lệ, fallback về 2d.")
        mode = "2d"

    # Bộ lệnh netconvert tương thích SUMO 1.24.0+
    cmd = [
        "netconvert",
        "--osm-files", osm_file,
        "-o", output_net_file,

        # --- BỀ RỘNG LÀN ---
        # OSM thường không khai báo width → netconvert dùng mặc định 3.2m.
        # Nới lên 4.0m để xe (to gần bằng lòng đường) còn chỗ lái.
        "--default.lanewidth", "3.2",  # Mặc định của netconvert

        # --- LÀM GỌN VÀ TỐI ƯU MẠNG LƯỚI ---
        "--geometry.remove",
        "--roundabouts.guess",
        "--ramps.guess",
        "--junctions.join",
        "--tls.guess-signals",
        "--tls.discard-simple",
        "--tls.join",

        # --- LỐI ĐI BỘ (cần cho route gen pedestrian) ---
        "--sidewalks.guess",
        "--crossings.guess",
    ]

    if mode == "3d":
        cmd += [
            "--osm.elevation",                # Lấy cao độ từ OSM nếu có
            "--osm.layer-elevation", "5",     # Nâng mỗi layer (cầu vượt) lên 4 mét
        ]

    print(f"\n[Thông báo] Đang chạy netconvert (mode = {mode.upper()})...")

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True,
                                encoding='utf-8', errors='replace')
        if result.stdout:
            print(result.stdout)
        print(f"\n[Thành công] Đã xuất bản đồ ra tệp: {output_net_file}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n[Lỗi] netconvert thất bại với mã {e.returncode}.")
        if e.stderr:
            print(e.stderr)
        return False
    except FileNotFoundError:
        print("\n[Lỗi] Không tìm thấy 'netconvert'. Cần cài đặt SUMO và thêm vào PATH.")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Tạo bản đồ từ OSM (2D/3D)")
    parser.add_argument("osm_file", help="Đường dẫn đến tệp .osm (vd: map.osm)")
    parser.add_argument("-o", "--output", dest="output_net_file", help="Tùy chọn: Tên tệp đầu ra")
    parser.add_argument("-m", "--mode", choices=["2d", "3d"], default="3d",
                        help="2d (phẳng) hoặc 3d (giữ cao độ). Mặc định: 3d")

    args = parser.parse_args()
    convert_osm_to_net_3d_roads(args.osm_file, args.output_net_file, mode=args.mode)