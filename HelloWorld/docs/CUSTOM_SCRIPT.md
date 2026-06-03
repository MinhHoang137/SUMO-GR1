# Custom Script Mode — Lưu ý vận hành

Chế độ **Custom Script** trong launcher cho phép người dùng tự dựng kịch bản
SUMO bằng `netedit` rồi đưa vào hệ thống chạy mô phỏng — không sinh route tự
động và không ghép Benchmark/VRP.

## Yêu cầu thư mục kịch bản

Khi chọn "Custom Script (folder)" ở launcher, đường dẫn được chọn phải là 1
**thư mục** chứa tối thiểu các file sau:

- `*.sumocfg` — cấu hình SUMO (nên có để xác định cặp net/route đúng)
- `*.net.xml` — mạng lưới đường (xuất từ `netedit`)
- `*.rou.xml` — định nghĩa flow / trip / route

Quy tắc dò file của helper `Server/custom_script.py`:

1. Ưu tiên đọc `.sumocfg` đầu tiên trong folder → lấy giá trị `net-file` và
   `route-files` để biết cặp file đúng (nếu folder chứa nhiều file cùng đuôi).
2. Nếu không có `.sumocfg`, hoặc tham chiếu sai/thiếu, **fallback dò file đầu
   tiên đúng đuôi** (theo thứ tự sắp xếp tên).
3. Copy `net` → `Server/SUMO_xml/HelloWorld.net.xml`
4. Copy `rou` → `Server/SUMO_xml/HelloWorld.rou.xml`
5. Ghi đè `Server/SUMO_xml/HelloWorld.sumocfg` chuẩn (trỏ tới 2 file trên).

Vì `traci.start` và các Reader (`CrossRoadReader`, `EdgeReader`,
`CrossingReader`, `unity_vehicle`) đều hard-code đường dẫn `SUMO_xml/HelloWorld.*`,
bước copy này là bắt buộc để tích hợp được kịch bản user-provided.

## Những gì bị vô hiệu hóa ở Custom Script

- Toàn bộ tham số sinh route Benchmark (num_pairs, car_cr_type, has_ped,
  ped_cr_type, ped_impatience).
- Toàn bộ tham số VRP (num_clients, num_staff).
- Tham số `Num Lanes` (chỉ áp dụng cho file `.map`).

Launcher giữ nguyên các nhóm UI nhưng **disable**; server-side bỏ qua hoàn toàn
nhánh sinh route trong `initialize_map_and_routes` qua check
`config.get("custom")`.

## Những gì vẫn áp dụng

- Render mode: Realtime / Pre-render
- Run with GUI (khởi động Unity Client tự động)
- Monitor (status + time step) trong launcher

## Workflow khuyến nghị khi có file .osm

1. Chạy `osm_launcher.py` để chuyển `.osm` → `.net.xml` 3D (gọi `netconvert`).
2. Mở `.net.xml` đó trong `netedit`, chỉnh sửa, thêm route, lưu lại
   `.rou.xml` + `.sumocfg`.
3. Đưa cả 3 file vào 1 thư mục, mở launcher chính → chọn "Custom Script
   (folder)" → trỏ tới thư mục đó → Start Server.

## Code OSM cũ (DEPRECATED nhưng không xóa)

Các thành phần sau vẫn còn trong codebase, được đánh dấu DEPRECATED nhưng giữ
lại làm tham chiếu hoặc phục vụ `osm_launcher.py` / chạy `main.py` trực tiếp:

- `Server/osm/osm_to_net.py` — convert `.osm` → `.net.xml` (osm_launcher.py dùng).
- `Server/SUMO_xml/route_gen.py::create_routes_osm` — pre-compute Dijkstra
  routes cho OSM network (thay vì TAZ routing).
- Nhánh `if maze_file.lower().endswith(".osm")` trong:
  - `Server/render/realtime_render.py::initialize_map_and_routes`
  - `Server/render/pre_render.py::initialize_map_and_routes`
  - (cả ở nhánh benchmark và VRP)

Các nhánh này chỉ kích hoạt khi gọi `main.py <path_to_.osm>` trực tiếp ngoài
launcher; launcher chính sẽ không bao giờ đẩy `.osm` xuống server nữa.
