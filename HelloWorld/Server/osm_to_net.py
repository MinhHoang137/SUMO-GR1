# DEPRECATED khỏi pipeline launcher chính (kể từ khi OSM trong launcher được thay
# bằng Custom Script). File này vẫn được osm_launcher.py dùng để dựng .net.xml 3D
# từ .osm như một công cụ phụ trợ — đừng xóa.

import os
import argparse
import subprocess

def convert_osm_to_net_3d_roads(osm_file, output_net_file=None):
    if not os.path.exists(osm_file):
        print(f"[Lỗi] Không tìm thấy tệp đầu vào (OSM): {osm_file}")
        return False

    if output_net_file is None:
        # Nếu không truyền tên file đầu ra, tự động lấy tên file osm thêm đuôi .net.xml
        output_net_file = os.path.splitext(osm_file)[0] + ".net.xml"

    # Bộ lệnh netconvert tương thích SUMO 1.24.0+
    cmd = [
        "netconvert",
        "--osm-files", osm_file,
        "-o", output_net_file,

        # --- CAO ĐỘ 3D (SUMO 1.24.0: chỉ có 2 option này) ---
        "--osm.elevation",                    # Lấy cao độ từ OSM nếu có
        "--osm.layer-elevation", "4",         # Nâng mỗi layer (cầu vượt) lên 4 mét

        # --- LÀM GỌN VÀ TỐI ƯU MẠNG LƯỚI ---
        "--geometry.remove",
        "--roundabouts.guess",
        "--ramps.guess",
        "--junctions.join",
        "--tls.guess-signals",
        "--tls.discard-simple",
        "--tls.join",
    ]

    print(f"\n[Thông báo] Đang chạy lệnh tạo bản đồ từ OSM...")

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
    parser = argparse.ArgumentParser(description="Tạo bản đồ đường 3D từ OSM")
    parser.add_argument("osm_file", help="Đường dẫn đến tệp .osm (vd: map.osm)")
    parser.add_argument("-o", "--output", dest="output_net_file", help="Tùy chọn: Tên tệp đầu ra")

    args = parser.parse_args()
    convert_osm_to_net_3d_roads(args.osm_file, args.output_net_file)