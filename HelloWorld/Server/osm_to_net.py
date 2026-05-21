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

    # Bộ lệnh netconvert tối ưu chỉ để tạo đường 3D
    cmd = [
        "netconvert",
        "--osm-files", osm_file,
        "-o", output_net_file,
        
        # --- CẤU HÌNH BẮT BUỘC ĐỂ TẠO ĐƯỜNG 3D ---
        "--osm.elevation", "true",        # Lấy cao độ trực tiếp (nếu OSM có)
        "--osm.layer-elevation", "4",     # Quan trọng nhất: Nâng mỗi layer (cầu vượt) lên 4 mét
        "--elevation.guess", "true",      # Bắt buộc: Tự động vuốt độ dốc cho các lối lên xuống cầu/hầm
        
        # --- LÀM GỌN VÀ TỐI ƯU MẠNG LƯỚI ---
        "--geometry.remove", "true",
        "--roundabouts.guess", "true",
        "--ramps.guess", "true",
        "--junctions.join", "true",
        "--tls.guess-signals", "true",
        "--tls.discard-simple", "true",
        "--tls.join", "true"
    ]
    
    print(f"\n[Thông báo] Đang chạy lệnh tạo ĐƯỜNG 3D...")
    
    try:
        subprocess.run(cmd, check=True)
        print(f"\n[Thành công] Đã xuất bản đồ đường 3D ra tệp: {output_net_file}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n[Lỗi] Lệnh thất bại với mã {e.returncode}.")
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