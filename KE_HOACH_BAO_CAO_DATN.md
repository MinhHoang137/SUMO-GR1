# Kế hoạch viết Báo cáo Đồ án Tốt nghiệp
### Hệ thống mô phỏng & hiển thị giao thông 3D từ SUMO trong Unity (dự án `HelloWorld`)

> Tài liệu này là **kế hoạch viết** (không phải bản thảo cuối). Nó ánh xạ cấu trúc template
> `SOICT_DATN_Application_VIE_Template`, chỉ rõ nội dung nào tái sử dụng từ `Report_old`,
> nội dung nào phải viết mới từ dự án `HelloWorld`, và đặc biệt liệt kê **17 use case** để
> đưa vào Chương 2 (yêu cầu của đề bài: 10–20 use case).

---

## 1. Nguồn tài liệu & nguyên tắc

| Nguồn | Vai trò trong báo cáo |
|-------|------------------------|
| `SOICT_DATN_Application_VIE_Template/` | Khung chương, định dạng, quy ước trình bày (ISO 7144). Bám sát tuyệt đối. |
| `Report_old/Chuong/*.tex` | Nội dung đã viết tốt cho Chương 1, 3, 5 → **tái sử dụng & cập nhật**. |
| `HelloWorld/` (mã nguồn + `CLAUDE.md`) | Nguồn sự thật cho chức năng, kiến trúc, use case, kết quả thực nghiệm. |

> **Cấu trúc thư mục mã nguồn chính (`HelloWorld/`):**
> - `Server/` — mã nguồn Python (TraCI, điều phối mô phỏng, giao tiếp TCP).
> - `TestGR1.1/` — Unity client (hiển thị 3D, tương tác lái xe).

**Khác biệt quan trọng cần xử lý:** `Report_old` mô tả hệ thống *hiển thị 3D cơ bản* (SUMO→TraCI/Python→Unity).
Nhưng `HelloWorld` đã mở rộng đáng kể: **chiếm quyền điều khiển xe (takeover), va chạm → sinh xác xe (wreck),
trả quyền & re-anchor, người đi bộ 3D, hai chế độ Realtime/Pre-render, nhập bản đồ OSM, nạp kịch bản tự dựng từ netedit, chế độ VRP**.
→ Báo cáo mới phải bổ sung các chức năng này, đặc biệt vào Chương 2 (use case), Chương 4 (thiết kế) và Chương 5 (đóng góp).

---

## 2. Cấu trúc báo cáo theo template

| Chương | Tiêu đề (template) | Trạng thái nội dung | Nguồn |
|--------|--------------------|---------------------|-------|
| 1 | GIỚI THIỆU ĐỀ TÀI | ~90% sẵn, chỉ rà lại phạm vi | `Report_old/1_Gioi_thieu.tex` |
| 2 | KHẢO SÁT VÀ PHÂN TÍCH YÊU CẦU | **Phải viết mới** (cũ chỉ là template rỗng) | Mã nguồn `HelloWorld` → mục 3–5 dưới đây |
| 3 | NỀN TẢNG LÝ THUYẾT VÀ CÔNG NGHỆ | ~95% sẵn, bổ sung Unity physics/WheelCollider | `Report_old/3_Cong_nghe.tex` |
| 4 | PHÂN TÍCH THIẾT KẾ, TRIỂN KHAI & ĐÁNH GIÁ | Viết mới phần thiết kế chi tiết + thực nghiệm | `Report_old/4_*.tex` (khung) + `HelloWorld` |
| 5 | CÁC GIẢI PHÁP & ĐÓNG GÓP NỔI BẬT | ~80% sẵn, **bổ sung takeover/wreck/re-anchor** | `Report_old/5_Giai_phap_dong_gop.tex` |
| 6 | KẾT LUẬN & HƯỚNG PHÁT TRIỂN | Cập nhật theo kết quả mới | `Report_old/6_Ket_luan.tex` |
| PL A | Hướng dẫn viết ĐATN | Giữ nguyên template | Template |
| PL B | Đặc tả use case (đầy đủ) | **Viết mới** từ mục 6 dưới đây | `HelloWorld` |

---

## 3. Tác nhân (Actors)

1. **Người dùng (User)** — tác nhân chính, một người duy nhất cho mỗi phiên: cấu hình kịch bản, khởi chạy mô phỏng, quan sát, điều khiển camera, tạm dừng/tiếp tục, xuất kết quả; **và** chiếm quyền điều khiển một xe để lái thủ công khi muốn.
2. **SUMO Server (tác nhân phụ — hệ thống ngoài)** — sinh dữ liệu mô phỏng vi mô, nhận lệnh điều khiển qua TraCI.

> **Quyết định mô hình hóa:** hệ thống là **một người – một phiên**, nên KHÔNG tách "người vận hành" và "người lái" thành hai actor (dễ hiểu nhầm là hai người khác nhau). Chỉ dùng **một actor "Người dùng"**; "lái xe" là một chế độ tương tác của chính người dùng đó. Đã áp dụng trong Chương 2.

---

## 4. Nhóm chức năng (use case mức cao — Biểu đồ tổng quát)

Bốn nhóm để phân rã:

- **A. Chuẩn bị kịch bản & bản đồ** (UC1–UC6)
- **B. Vận hành mô phỏng** (UC7–UC9) — UC7/UC8 «include» hiển thị xe, đèn, người đi bộ
- **C. Quan sát & điều khiển** (UC10–UC13)
- **D. Lái xe tương tác** (UC14–UC15)
- **E. Kết quả & lưu trữ** (UC16–UC17)

---

## 5. Danh sách 17 use case (đưa vào Chương 2 — mục 2.2)

| # | Use case | Tác nhân | Mô tả ngắn | Bằng chứng trong mã nguồn |
|---|----------|----------|------------|---------------------------|
| UC1 | Tạo bản đồ benchmark từ mê cung | Người dùng | Nạp lưới ký tự `.map` (`@`=tường, `.`=lối đi), vét cạn node → sinh `.nod/.edg/.con.xml` | `Server/naive_map_creator.py`, `SUMO_xml/` |
| UC2 | Nhập bản đồ từ OpenStreetMap | Người dùng | Chọn `.osm` → tự build `.net.xml`/`.rou.xml`/`.sumocfg` (Tab OSM) | `osm_launcher.py`, `launcher.py` (Tab 2) |
| UC3 | Nạp kịch bản tự dựng từ netedit | Người dùng | Chọn thư mục chứa `.net.xml` + `.rou.xml` do người dùng tạo bằng netedit → launcher xác thực & khởi chạy (Tab Custom Script) | `launcher.py` (Tab 3), `Server/custom_script.py`, `main.py` (`is_custom`) |
| UC4 | Sinh tuyến đường cho xe | Người dùng | Chọn kiểu phân chia OD (CS/SS/IO/OI), lọc cặp khả thi bằng BFS | `Server/main.py`, `SUMO_xml/route_gen.py` |
| UC5 | Sinh tuyến đường cho người đi bộ | Người dùng | Bật/tắt người đi bộ, đặt `impatience` tại điểm qua đường | `main.py` (`has_ped`, `ped_impatience`) |
| UC6 | Cấu hình tham số mô phỏng | Người dùng | Số làn, số cặp nút, chế độ GUI, chế độ render | `launcher.py`, `main.py` (`setup_simulation_config`) |
| UC7 | Chạy mô phỏng chế độ Realtime | Người dùng | Stream trạng thái mỗi step qua TCP, Unity hiển thị tức thời; «include» hiển thị xe 3D, đèn giao thông, người đi bộ | `render/realtime_render.py`, `Simulation/Realtime/`, `TrafficerManager.cs`, `trafficLight.py`, `crossing.py` |
| UC8 | Chạy mô phỏng chế độ Pre-render (replay) | Người dùng | Ghi `scenario.json` (từng step) rồi phát lại trong Unity; «include» hiển thị xe 3D, đèn giao thông, người đi bộ | `render/pre_render.py`, `render/scenario_recorder.py`, `Simulation/PreRender/` |
| UC9 | Chạy mô phỏng với SUMO-GUI | Người dùng | Bật cửa sổ sumo-gui song song để đối chiếu | `launcher.py` (`run_with_gui`) |
| UC10 | Điều khiển camera quan sát | Người dùng | Camera tự do / bám xe, đổi chế độ | `UI/CameraController.cs`, `CameraControllerUI.cs` |
| UC11 | Tạm dừng / tiếp tục mô phỏng | Người dùng | Gửi lệnh Pause/Resume qua kênh điều khiển; người đi bộ không trôi khi pause | `Simulation/Realtime/PauseSO`, `realtime_render.py` |
| UC12 | Điều chỉnh tốc độ mô phỏng | Người dùng | Đổi `timeStep`/hệ số tốc độ lúc đang chạy | `UI/SpeedMultiplierUI.cs`, `Traffic/SpeedMultiplier.cs` |
| UC13 | Lọc đối tượng hiển thị theo vùng | Người dùng | Cull đối tượng ngoài tầm để tối ưu hiệu năng | `Optimization/FilterTransform.cs`, `FilterUI.cs` |
| UC14 | Chiếm quyền điều khiển & lái xe thủ công | Người dùng | Chọn xe server → `TakeControl` → lái bằng bàn phím (physics) | `UnityVehicle.cs`, `WheelController.cs`, `UI/VehicleTakeoverUI.cs` |
| UC15 | Trả quyền điều khiển xe | Người dùng | Thả xe → xe bị hủy ngay khỏi SUMO (không re-anchor); xe bị tông → thành xác xe (UC16) | `UnityVehicle.ReleaseControl`, `Server/Traffic/unity_vehicle.py` (state 1 → `_remove_vehicle`) |
| UC16 | Gây va chạm sinh xác xe | Người dùng | Va chạm vật lý → `BecomeWreck`, xe mất điều khiển, despawn sau N bước | `UnityVehicle.OnCollisionEnter`, `unity_vehicle.py` (state 3) |
| UC17 | Ghi & lưu trữ phiên mô phỏng | Người dùng | `SimulationSession` gom `trips.csv`, `summary.json`, `road_data.json`, `scenario.json` vào `result/{map}-{timestamp}/`; realtime cũng phát lại được | `render/scenario_recorder.py` |

> **Tổng: 17 use case** (trong khoảng 10–20 theo yêu cầu). UC7/UC8 đã «include» hành vi hiển thị xe, đèn, người đi bộ — các hành vi này là side effect tự động của hệ thống, không phải hành động của người dùng, nên không tách thành use case riêng.

---

## 6. Use case đặc tả chi tiết (mục 2.3 + Phụ lục B)

Template yêu cầu đặc tả chi tiết **4–7 use case quan trọng nhất** (tên, luồng chính/phụ, tiền/hậu điều kiện).
Chọn 6 use case "xương sống" và có luồng phát sinh phong phú:

1. **UC7 – Chạy mô phỏng Realtime** (luồng phụ: mất kết nối TCP, gói JSON phân mảnh).
2. **UC4 – Sinh tuyến đường cho xe** (luồng phụ: cặp OD không liên thông → lọc bỏ).
3. **UC14 – Chiếm quyền & lái xe** (luồng phụ: xe đang lái bị tông → latch `hasCrashed`).
4. **UC15 – Trả quyền** (luồng chính: xe bị hủy ngay; luồng phụ: xe đã bị tông → thành xác xe thay vì hủy trực tiếp).
5. **UC11 – Tạm dừng/tiếp tục** (đồng bộ `pause_event` ↔ Unity, người đi bộ không trôi).
6. **UC2 – Nhập bản đồ OSM** (luồng phụ: OSM lỗi/không build được mạng).

> Vẽ **biểu đồ hoạt động** kèm theo cho UC14 và UC15. UC15 đã đơn giản hơn: không còn nhánh "tìm làn / trong ngưỡng?"; chỉ còn hai nhánh: đã va chạm → `BecomeWreck`, chưa va chạm → hủy xe ngay (`_remove_vehicle`, Unity recycle). Cập nhật lại `fig:act-uc15` và `fig:reanchor-flow`.

---

## 7. Phân bổ nội dung & việc cần làm theo chương

### Chương 1 — Giới thiệu (tái sử dụng)
- Giữ 4 mục: Đặt vấn đề, Mục tiêu & phạm vi, Định hướng giải pháp, Bố cục.
- **Cập nhật:** thêm 1 câu vào "Mục tiêu" nêu tính tương tác (lái xe, va chạm) như điểm mở rộng so với hiển thị thuần túy.

### Chương 2 — Khảo sát & yêu cầu (VIẾT MỚI — trọng tâm đề bài)
- 2.1 Khảo sát hiện trạng: so sánh sumo-gui (2D) vs CARLA vs giải pháp đề xuất (bảng so sánh).
- 2.2 Tổng quan chức năng: biểu đồ use case tổng quát + 5 biểu đồ phân rã (nhóm A–E ở mục 4).
- 2.3 Đặc tả chi tiết 6 use case (mục 6).
- 2.4 Yêu cầu phi chức năng: hiệu năng (object pooling, FilterTransform, DrawCallsReducer), độ tin cậy (TCP framing `<END>`, shutdown gọn), tính mở rộng (data contract độc lập engine).

### Chương 3 — Công nghệ (tái sử dụng)
- Giữ nguyên SUMO/TraCI/Python/Unity.
- **Bổ sung tiểu mục:** Unity Physics (Rigidbody, WheelCollider) phục vụ chế độ lái — vì `Report_old` chưa đề cập.

### Chương 4 — Thiết kế, triển khai & đánh giá (viết mới phần lớn)
- Kiến trúc tổng thể: sơ đồ SUMO ↔ TraCI/Python ↔ (3 cổng TCP 5050/5053/5054) ↔ Unity.
- Thiết kế module Unity: Network, Traffic (Trafficer/TrafficLight), UnityVehicle, Optimization, UI.
- Máy trạng thái `ExistState` (4 trạng thái) — lấy từ `HelloWorld/CLAUDE.md`.
- Thực nghiệm: kịch bản benchmark theo kích thước mê cung, OSM thật, đo FPS/độ trễ, ảnh chụp màn hình.

### Chương 5 — Giải pháp & đóng góp (tái sử dụng + bổ sung)
- Giữ 5 giải pháp cũ (TCP framing, điều phối đa luồng, sinh mạng vét cạn, sinh route + lọc BFS, chuẩn hóa TraCI).
- **Cập nhật giải pháp "ghi log":** đổi từ CSV/JSON rời rạc sang mô hình **phiên hợp nhất `SimulationSession`** (`render/scenario_recorder.py`) — một thư mục `result/{map}-{timestamp}/` chứa `trips.csv` + `summary.json` + `road_data.json` + `scenario.json`; ghi `scenario.json` dạng streaming có buffer 10MB; realtime nay cũng ghi lại được để phát lại như pre-render.
- **Bổ sung 2 giải pháp mới (điểm nhấn ĐATN):**
  - 5.x Cơ chế **takeover hybrid** (kinematic↔dynamic, khóa điều khiển bằng `existState`, upload batch).
  - 5.y Cơ chế **wreck + hủy xe khi thả quyền** (đếm despawn tập trung chống cull; khi thả quyền không va chạm → `_remove_vehicle` ngay, không tìm đường).

#### [ĐỀ XUẤT THÊM — CHỜ CÂN NHẮC] 5.z Tối ưu luồng dữ liệu SUMO↔Unity
> Nguồn: `HelloWorld/KE_HOACH_TOI_UU_LUONG_DU_LIEU.md` (đã hiện thực + đo). Có số liệu thật nên hợp
> làm một mục giải pháp/đóng góp. Chương 6 đã nhắc tới (kết quả + hạn chế) nhưng Chương 5 chưa giải
> thích *cách làm*. Gắn được với `tab:perf` Chương 4.

Bốn giải pháp con (xếp theo lợi ích/công sức):
1. **Gom truy vấn TraCI bằng subscription** — thay N×k lệnh riêng/bước bằng 1 lần `subscribe` +
   `getAllSubscriptionResults()` (~1 round-trip). Đo (~90 xe, 200 bước, localhost): **3769 ms → 372 ms (~10×)**,
   2763 phép đọc, **0 sai lệch**. File `Server/Traffic/trafficer.py`.
2. **Nén luồng trạng thái** — raw-DEFLATE+base64, tiền tố `GZ:`, giữ nguyên khung `<END>`, có cờ
   `COMPRESS_DOWNLOAD`, tương thích ngược. Đo ~3× (float ngẫu nhiên; SUMO thật cao hơn).
   File `Server/network.py`, Unity `Network.MaybeDecompress`.
3. **Sửa rớt frame + bỏ quét O(n²)** ở `Network.ReadMessage` (Unity): buffer bền per-connection,
   giữ phần dư sau `<END>`, quét marker theo offset. Sửa luôn bug TCP gộp gói làm mất bản tin.
4. **TCP_NODELAY (tắt Nagle) + giảm cấp phát** — `setsockopt`/`client.NoDelay`; tái dùng list trong
   `ProcessData`. File `Server/network.py`, Unity `Network.cs`, `TraffiicerManager.cs`.

Kèm **cơ chế đo độ trễ đầu–cuối**: Python đóng dấu `"ts"` lúc gửi, Unity tính `LatencyMs` + hiển thị
`LatencyText`; chạy thuần một máy nên trừ trực tiếp, không cần đồng bộ đồng hồ → điền `tab:perf`.

**Bảng số liệu gợi ý:** đọc trạng thái/bước 3769→372 ms (~10×); payload/bước ~3×; rớt frame: có→**0**;
độ trễ đầu–cuối: đo được theo N xe.

**CHƯA làm (giữ ở Chương 6 — hướng phát triển, đừng ghi như đã đạt):** định dạng nhị phân (MessagePack),
delta encoding, lọc theo vùng quan sát (AoI). Lưu ý xe client-owned (đang lái/xác xe) KHÔNG được lọc dù xa camera.

> Định hướng khi viết: nhấn mạnh **thay đổi vừa phải, có cờ bật/tắt, tương thích ngược** — không phải
> tối ưu đánh đổi rủi ro cao.

### Chương 6 — Kết luận
- Cập nhật đóng góp đạt được (gồm tính tương tác: chiếm quyền/lái xe, va chạm, re-anchor; lưu & phát lại phiên).
- Hướng phát triển: hỗ trợ **đa người dùng đồng thời** (nhiều client cùng một phiên mô phỏng), mở rộng loại phương tiện, đánh giá định lượng (FPS/độ trễ theo quy mô mạng), cải thiện re-anchor & vật lý lái.
- **Lưu ý phân định hiện trạng vs hướng phát triển:** hiện tại hệ thống chạy **thuần một máy, một người – một phiên** (server stream cho đúng một client Unity). Không dùng tính năng phát mô phỏng từ xa. Đa người dùng đồng thời là **tính năng chưa có**, chỉ nêu ở mục hướng phát triển — không mô tả như đã đạt được.

---

## 8. Hình vẽ & bảng cần bổ sung

**Trạng thái:** ✅ = xong/đạt; 🟡 = đã vẽ **nháp bằng TikZ** trong báo cáo (đủ ý, chưa
trau chuốt) — cần vẽ lại đẹp bằng công cụ UML (draw.io / StarUML / PlantUML) trước khi nộp.

- 🟡 Biểu đồ use case tổng quát + 5 biểu đồ phân rã (nhóm A–E) — **đã vẽ nháp TikZ** trong Chương 2
  (Hình `fig:uc-tongquat`, `fig:uc-nhomA..E`). Actor hiện là hình que TikZ; bố cục thẳng hàng đơn giản.
  Cần vẽ lại: gom nhóm gọn hơn, thêm quan hệ «include»/«extend» nếu cần, canh đẹp.
- 🟡 Biểu đồ hoạt động UC14 (lái xe) và UC15 (trả quyền/re-anchor) — **đã vẽ nháp TikZ**
  (Hình `fig:act-uc14`, `fig:act-uc15`). Cần vẽ lại đẹp, thêm swimlane nếu muốn phân vai Unity/SUMO.
- ✅ Bảng so sánh công cụ mô phỏng (mục 2.1, `tab:khaosat-sosanh`) — đã có, dùng được luôn.
- 🟡 Sơ đồ kiến trúc tổng quát + vòng lặp TraCI (Chương 3, `fig:congnghe-architecture`, `fig:traci-loop`)
  — **đã vẽ nháp TikZ**; vẽ lại đẹp khi hoàn thiện.
- 🟡 Minh họa 2 thuật toán dựng bản đồ (Chương 5): dải mặt đường + miter (`fig:edge-ribbon`),
  tam giác hóa → đùn khối nút giao (`fig:junction-prism`) — **nháp TikZ**; kèm mã giả
  `alg:edge`, `alg:junction` (algorithm2e). Có thể chụp ảnh thật từ Unity để minh họa thêm.
- 🟡 Sơ đồ kiến trúc chi tiết 3 cổng TCP + 2 luồng dữ liệu (Chương 4, `fig:arch-detail`) — **đã vẽ nháp TikZ**.
- 🟡 Biểu đồ máy trạng thái `ExistState` (Chương 4, `fig:existstate`) — **đã vẽ nháp TikZ**.
- [ ] **Ảnh chụp** (Chương 4): cảnh 3D, đèn, người đi bộ, chế độ lái, xác xe — đang để khung `[Chèn ảnh]` (`fig:demo-scene`, `fig:demo-drive`).
- [ ] **Số liệu thực nghiệm** (Chương 4, `tab:perf`): tốc độ khung hình theo số xe, độ trễ — bảng đang để trống, cần đo và điền.

> **Ghi chú vẽ nháp (theo yêu cầu):** mọi biểu đồ trong Chương 2 đều gắn caption "(bản nháp)".
> Chúng compile được và truyền đạt đúng nội dung, nhưng là bản phác — khi hoàn thiện nên thay
> bằng hình vẽ chỉn chu hơn rồi bỏ chữ "(bản nháp)" trong caption.

---

## 9. Thứ tự thực hiện (theo yêu cầu GVHD: viết Tóm tắt & Kết luận trước)

1. ✅ Dựng cây thư mục báo cáo từ template (`BaoCao_DATN/`), biên dịch được.
2. ✅ Viết Chương 0 (Lời cảm ơn, Tóm tắt) và Chương 1 (Giới thiệu).
3. **Viết Chương 6 (Kết luận & hướng phát triển)** — GVHD yêu cầu làm sớm cùng Tóm tắt,
   vì hai phần này định khung "đã làm gì / đạt gì / còn gì" cho cả báo cáo.
4. ✅ Viết Chương 2 (use case) — gồm 17 use case, đặc tả chi tiết 6 use case + biểu đồ nháp.
5. ✅ Viết Phụ lục B (đặc tả đầy đủ 11 use case còn lại).
6. ✅ Viết Chương 3 (công nghệ) — tái sử dụng + bổ sung mục Unity Physics & luồng 2 chiều.
7. ✅ Viết Chương 4 (thiết kế + thực nghiệm) — kiến trúc 3 cổng, máy trạng thái, module, kiểm thử.
   **Còn thiếu (cần làm tay):** chụp ảnh màn hình (`fig:demo-*`) và đo + điền số liệu hiệu năng (`tab:perf`).
8. ✅ Viết Chương 5 (giải pháp & đóng góp) — 7 mục: dựng bản đồ (Junction+Edge), chiếm quyền,
   va chạm, re-anchor, lưu trữ/phát lại, TCP framing, tối ưu hiệu năng. 3 mục đánh dấu `[ĐỀ XUẤT THÊM]`.
9. Rà soát chéo tham chiếu, hình/bảng, danh mục viết tắt (SUMO, TraCI, OD, VRP, OSM…).

---

## 10. Cách đo độ trễ giữa Python và Unity (cho `tab:perf`)

> Phạm vi đồ án: hệ thống chạy **thuần một máy** (không dùng phát mô phỏng từ xa). Do hai
> tiến trình Python và Unity đọc chung một đồng hồ hệ thống, có thể đo độ trễ một chiều bằng
> cách trừ trực tiếp `t_recv − t_send`, không cần kỹ thuật khứ hồi/đồng bộ đồng hồ.

### Đo một chiều (gửi → đã hiển thị)

1. **Python (phía gửi):** ngay trước khi gửi mỗi gói trạng thái, đóng dấu thời gian vào payload.
   Trong `realtime_render.py`, vòng `run_simulation`, chỗ tạo `data`:
   ```python
   import time
   data["ts"] = time.time() * 1000.0   # mốc gửi, đơn vị mili-giây
   network.send_data(client_socket, data)
   ```
2. **Unity (phía nhận):** khi áp dụng gói lên scene (main thread, trong `TrafficDataListener`/
   `TrafficerManager.ProcessData`), lấy giờ hiện tại cùng hệ quy chiếu epoch:
   ```csharp
   double nowMs = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds();
   double latency = nowMs - data.ts;   // mili-giây
   ```
3. Gom `latency` vào danh sách → tính **trung bình, trung vị, p95** và ghi ra file. Đó là độ
   trễ đầu–cuối (gửi → đã hiển thị).

### Bóc tách thành phần độ trễ (nếu muốn phân tích sâu)
Đặt nhiều mốc thời gian để tách: (i) **serialize** ở Python (`json.dumps`), (ii) **truyền TCP +
tách khung `<END>`** (mốc trên thread nhận của Unity ngay khi ghép đủ 1 bản tin), (iii) **chờ
main thread + parse + áp dụng** (mốc sau khi cập nhật scene). Hiệu hai mốc liên tiếp cho từng phần.

### Mẹo thực nghiệm
- Tắt `time_step` sleep (hoặc đặt nhỏ) khi đo để không lẫn thời gian "ngủ" giữa các bước vào độ trễ.
- Đo ở nhiều mức số lượng xe (gắn với `tab:perf`) để thấy độ trễ tăng theo tải.
- Đo FPS song song: ghi `1/Time.deltaTime` trong Unity, lấy trung bình theo cùng các mốc tải.
