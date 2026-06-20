# Kế hoạch viết lại Mục 4.1 và 4.2 — Bổ sung module dựng bản đồ

> **Phạm vi:** chỉ chỉnh sửa `BaoCao_DATN/Chuong/4_Ket_qua_thuc_nghiem.tex` và cập nhật
> `DiagramsCode/hinh4.2.drawio` (+ regenerate PNG). Không chạm các mục 4.3–4.5.
>
> **Lý do thay đổi:**
> - Sơ đồ hinh4.2 thiếu nhóm module "Dựng bản đồ 3D" phía Unity.
> - Mục 4.2 mô tả mô phỏng & tương tác nhưng chưa có tiểu mục nào nói đến pipeline
>   sinh bản đồ 3D — cả phía Python (tạo `road_data.json`) lẫn phía Unity (4 Maker).

---

## 1. Thay đổi tại Mục 4.1 — Thiết kế kiến trúc

**Nguyên tắc:** giữ ~90% văn bản, chỉ bổ sung ở hai chỗ.

### 1a. Cập nhật sơ đồ hinh4.2 (drawio)

File: `DiagramsCode/hinh4.2.drawio`

**Thêm một component box mới vào khối Unity:**

| Thuộc tính | Giá trị |
|-----------|---------|
| ID gợi ý | `ROAD` |
| Nhãn | `Dựng bản đồ 3D`<br>`(RoadDataListener · EdgeMaker · JunctionMaker · CrossingMaker · BuildingMaker)` |
| Style | giữ nguyên style component xanh như các box Unity khác |
| Vị trí gợi ý | hàng giữa khối Unity, bên dưới `UNET`, trên `TRAFFIC` — vì nhận dữ liệu từ Network và chạy trước Traffic |

**Thêm cạnh mới:**

| Nguồn | Đích | Nhãn | Style |
|-------|------|------|-------|
| `UNET` (Network Unity) | `ROAD` (Dựng bản đồ 3D) | `road_data.json (một lần)` | nét liền, màu như e8 |

> **Ghi chú về cổng:** `road_data` được gửi qua cổng **5050** (cổng chính), không phải một
> cổng riêng. `RoadDataListener` mở một kết nối TCP đến 5050, gửi `"RoadDataRequest"`, nhận
> gói dữ liệu mạng rồi đóng kết nối ngay. Sau đó `TrafficDataListener` mở kết nối thứ hai
> đến cùng cổng 5050 để nhận dữ liệu mô phỏng theo từng bước.
>
> **Lựa chọn đơn giản:** cập nhật nhãn cạnh e13 (PY→UN) từ `"5050: dữ liệu mô phỏng"` thành
> `"5050: dữ liệu mạng đường (một lần) + dữ liệu mô phỏng (mỗi bước)"` để không cần thêm cạnh.

Sau khi sửa drawio → export PNG → thay thế `BaoCao_DATN/Hinhve/hinh4.2-so-do-goi-module.png`.

### 1b. Cập nhật đoạn văn + bảng tab:unity-modules (trong tex)

**Hiện trạng:** đoạn văn phía Unity trong 4.1.3 chỉ có một câu dẫn vào bảng
(`"Phía Unity đảm nhiệm hiển thị và tương tác, gồm các nhóm mô-đun chính trình bày
trong Bảng X."`). Bảng có 6 hàng, **không có hàng nào về dựng bản đồ**.
Phía Python đã được mô tả chi tiết 6 nhóm bằng văn xuôi — phía Unity cần bổ sung
tương tự.

**Việc cần làm:**

1. **Thêm hàng vào bảng** — sau hàng "Mạng (Network)":
```latex
Dựng bản đồ 3D (Road) & Nhận dữ liệu mạng đường một lần khi khởi chạy;
dựng Mesh mặt đường, nút giao, vạch sang đường và công trình. \\
```

2. **Mở rộng đoạn văn phía Unity** — hiện chỉ 1 câu, bổ sung thêm câu mô tả
nhóm bản đồ (tương tự cách Python được mô tả bằng văn xuôi):

> "Trong đó, nhóm mô-đun \emph{Dựng bản đồ 3D} nhận dữ liệu mạng đường từ
> Python một lần khi khởi chạy và dựng lưới đa giác cho mặt đường, nút giao,
> vạch sang đường và công trình, tạo nên cảnh ba chiều nền cho toàn bộ phiên."

3. **Caption hình 4.1.2** — cân nhắc cập nhật caption từ `"Sơ đồ gói các nhóm
mô-đun hai phía và quan hệ phụ thuộc"` thành phản ánh đủ 7 nhóm Unity (sau khi
drawio được cập nhật).

---

## 2. Thay đổi tại Mục 4.2 — Thiết kế chi tiết

**Nguyên tắc:** viết lại tương đối nhiều. Cần thêm 2 tiểu mục mới và sửa lại tiểu mục cũ
"Thiết kế một số lớp chủ đạo". Các tiểu mục khác (máy trạng thái, hai luồng dữ liệu,
lưu trữ, giao diện) giữ nguyên văn bản.

### Cấu trúc mục 4.2 sau khi hoàn chỉnh

| # | Tiểu mục | Hình | Trạng thái |
|---|----------|------|-----------|
| 4.2.1 | **[MỚI]** Thiết kế module dựng bản đồ 3D | hinh4.2.1 (sơ đồ lớp Unity) | viết mới |
| 4.2.2 | Máy trạng thái điều khiển phương tiện | hinh4.2.2 | giữ nguyên |
| 4.2.3 | Hai luồng dữ liệu | hinh4.2.3 | giữ nguyên |
| 4.2.4 | Thiết kế một số lớp chủ đạo | hinh4.2.4 (Unity) + hinh4.2.5 (Python traffic, MỚI) | bổ sung đáng kể |
| 4.2.6 | Lưu trữ dữ liệu | hinh4.2.6 | giữ nguyên |
| 4.2.7 | Thiết kế giao diện người dùng | hinh4.2.7 | giữ nguyên |

---

### 2a. Tiểu mục mới 4.2.1 — Thiết kế module dựng bản đồ 3D

**Hình sơ đồ lớp cần vẽ:**

Vì Python không có class theo nghĩa UML chặt chẽ (module dựng bản đồ phía server
chủ yếu là hàm trong `render_map.py` + class `CrossingReader` trong `crossing.py`),
phía server mô tả bằng văn. Chỉ vẽ **sơ đồ lớp phía Unity**:

```
hinh4.2.1 — Sơ đồ lớp module dựng bản đồ 3D (phía Unity)
```

**Các lớp cần thể hiện:**

| Lớp | Stereotype | Thuộc tính chính | Phương thức chính |
|-----|-----------|-----------------|------------------|
| `RoadDataListener` | MonoBehaviour | -roadData: RoadDataSO; -networkSO: NetworkSO | +StartListening(); OnRoadDataReceived (event) |
| `RoadData` | (POCO) | +EdgeDatas, +JunctionDatas, +CrossingDatas, +BuildingDatas | — |
| `RoadDataSO` | ScriptableObject | +edgeDatas: List\<EdgeData\>; +junctionDatas; +crossingDatas; +buildingDatas | — |
| `EdgeMaker` | MonoBehaviour | -roadData: RoadDataSO; -edgePrefab: Edge | +BuildAll() |
| `JunctionMaker` | MonoBehaviour | -roadData: RoadDataSO; -crossRoadPrefab: Junction | +BuildAll() |
| `CrossingMaker` | MonoBehaviour | -roadData: RoadDataSO; -crossingPrefab: Crossing | +BuildAll() |
| `BuildingMaker` | MonoBehaviour | -roadData: RoadDataSO; -buildingPrefab: Building | +BuildAll() |

**Quan hệ:**
- `RoadDataListener` → writes → `RoadDataSO`
- `RoadDataListener` → deserializes → `RoadData` → copies into → `RoadDataSO`
- `EdgeMaker`, `JunctionMaker`, `CrossingMaker`, `BuildingMaker` → reads → `RoadDataSO` (dependency)
- `RoadDataSO` aggregates `EdgeData`, `JunctionData`, `CrossingData`, `BuildingData`

**File drawio:** `DiagramsCode/hinh4.2.1-so-do-lop-ban-do-unity.drawio`
> File `hinh4.2.1-pipeline-dung-ban-do.drawio` (sơ đồ luồng) đã xóa — không cần thiết vì 4.1.2 đã đóng vai trò tương tự.

**Nội dung văn tiểu mục 4.2.1 (khoảng 400 chữ):**

*Phía Python:* Khi SUMO khởi chạy, `render_map.py` gọi các API TraCI/sumolib để đọc
junctions (hình dạng nút giao), edges/lanes (đa tuyến trung tâm, chiều rộng),
`CrossingReader.read_crossings()` để đọc vạch sang đường, và đọc đa giác nhà từ OSM.
Dữ liệu được đóng gói thành một gói JSON và gửi qua cổng 5050 một lần khi Unity gửi
`"RoadDataRequest"`, đồng thời ghi ra `road_data.json` trong thư mục phiên.

*Phía Unity:* Mô tả cấu trúc các lớp (dựa vào bảng và sơ đồ hinh4.2.1). Pipeline hoạt
động theo thứ tự: kết nối → nhận → ghi SO → kích hoạt 4 Maker → dựng Mesh.

> **Phân biệt với Chương 5:** 4.2.1 mô tả *ai làm gì, cấu trúc lớp*. Chương 5 mô tả
> *thuật toán* (ribbon+miter, triangulation, prism). Không trùng lặp.

---

### 2b. Bổ sung đáng kể tiểu mục 4.2.4 — Thiết kế một số lớp chủ đạo

Tiểu mục hiện tại liệt kê 6 lớp Unity (TrafficerManager, UnityVehicle, WheelController,
VehicleSender, UnityVehicleManager, SimulationSession) và kèm hinh4.2.4 (sơ đồ lớp Unity).

**Cần bổ sung:**

**1. Sơ đồ lớp module giao thông phía Python server (hinh4.2.5 — hình mới):**

Python Traffic module có các class rõ ràng:

| Lớp / Module | Loại | Thuộc tính/Phương thức chính |
|-------------|------|------------------------------|
| `TrafficerData` | dataclass | id, obj_type, speed, position, forward; `to_dict()` |
| `TrafficLightData` | dataclass | id, position, state, direction; `to_dict()` |
| `CrossingReader` | class | `parse_shape()`, `read_crossings()` |
| `trafficer.py` (module) | — | `read_trafficers(traci)`, `_sync_subscriptions()` |
| `unity_vehicle.py` (module) | — | `process_vehicle_updates(traci)`, `_remove_vehicle()`, `_re_anchor()` |

Vì `trafficer.py` và `unity_vehicle.py` là module-level functions (không phải class),
dùng **component/package diagram** cho phần này thay vì class diagram thuần túy.
Kết hợp: vẽ class `TrafficerData`, `TrafficLightData`, `CrossingReader` + module
`trafficer` và `unity_vehicle` như component.

**File drawio:** `DiagramsCode/hinh4.2.5-so-do-lop-traffic-server.drawio`
**File PNG:** `BaoCao_DATN/Hinhve/hinh4.2.5-so-do-lop-traffic-server.png`

**2. Thêm bullet lớp Road vào danh sách văn bản (sau `SimulationSession`):**

```latex
\item \texttt{RoadDataListener} (Unity): kết nối cổng 5050, gửi yêu cầu
\texttt{"RoadDataRequest"}, nhận gói dữ liệu bản đồ một lần, ghi vào
\texttt{RoadDataSO} rồi đóng kết nối.
\item \texttt{EdgeMaker}, \texttt{JunctionMaker}, \texttt{CrossingMaker},
\texttt{BuildingMaker} (Unity): bốn lớp dựng Mesh từ \texttt{RoadDataSO};
mỗi lớp chịu trách nhiệm một loại đối tượng địa lý, chạy một lần.
\item \texttt{TrafficerData}, \texttt{TrafficLightData} (Python): lớp dữ liệu
đóng gói trạng thái phương tiện và đèn tín hiệu mỗi bước; \texttt{to\_dict()}
chuyển sang JSON để gửi qua TCP.
```

---

## 3. Kế hoạch đổi tên file (Renaming)

> **Phạm vi:** chỉ đổi tên file vật lý (PNG + drawio) để quản lý dễ hơn — tên file
> phản ánh vị trí section trong báo cáo. **Không thay đổi cách LaTeX đánh số hình**
> (giữ nguyên `\counterwithin{figure}{chapter}` trong `DoAn.tex` để đồng bộ với các
> chương khác). Label `\label{fig:...}` và `\ref{fig:...}` trong tex cũng giữ nguyên.
> Chỉ cần cập nhật đường dẫn trong `\includegraphics{...}`.

### 3a. Bảng đổi tên file — Hinhve/ (Chương 4)

| Số mới | File cũ (`Hinhve/`) | File mới (`Hinhve/`) | Trạng thái |
|--------|---------------------|----------------------|-----------|
| **4.1.1** | `hinh4.1-thiet-ke-kien-truc-chi-tiet.png` | `hinh4.1.1-thiet-ke-kien-truc-chi-tiet.png` | đổi tên |
| **4.1.2** | `hinh4.2-so-do-goi-module.png` | `hinh4.1.2-so-do-goi-module.png` | đổi tên + nội dung thay đổi (thêm module Road) |
| **4.2.1** | *(chưa có)* | `hinh4.2.1-so-do-lop-ban-do-unity.png` | **tạo mới** (sơ đồ lớp Unity map) |
| **4.2.2** | `hinh4.3-may-trang-thai-1-phuong-tien.png` | `hinh4.2.2-may-trang-thai-1-phuong-tien.png` | đổi tên |
| **4.2.3** | `hinh4.4-trinh-tu-trao-doi.png` | `hinh4.2.3-trinh-tu-trao-doi.png` | đổi tên |
| **4.2.4** | `hinh4.5-so-do-lop-unity.png` | `hinh4.2.4-so-do-lop-unity.png` | đổi tên |
| **4.2.5** | *(chưa có)* | `hinh4.2.5-so-do-lop-traffic-server.png` | **tạo mới** (lớp Python traffic) |
| **4.2.6** | `hinh4.6-cau-truc-thu-muc-phien.png` | `hinh4.2.6-cau-truc-thu-muc-phien.png` | đổi tên ✅ |
| **4.2.7** | `hinh4.7-bo-cuc-giao-dien.png` | `hinh4.2.7-bo-cuc-giao-dien.png` | đổi tên ✅ |
| **4.3.1** | `hinh4.8-anh-goc-nhin-3d-tu-tren-cao.png` | `hinh4.3.1-anh-goc-nhin-3d-tu-tren-cao.png` | đổi tên |
| **4.3.2a** | `hinh4.9.2-goc-nhin-cua-1-xe-tu-hanh-boi-may-chu.png` | `hinh4.3.2a-goc-nhin-cua-1-xe-tu-hanh-boi-may-chu.png` | đổi tên (subfigure a) |
| **4.3.2b** | `hinh4.9-goc-nhin-trong-xe.png` | `hinh4.3.2b-goc-nhin-trong-xe.png` | đổi tên (subfigure b) |
| **4.3.3** | `hinh4.10-va-cham-gay-un-tac.png` | `hinh4.3.3-va-cham-gay-un-tac.png` | đổi tên |

> Các hình ở chương khác (2, 3, 5) không đổi tên file vì tên file hiện chúng đã
> không có prefix `hinh4.` — chỉ đổi tên file chương 4.

### 3c. Bảng đổi tên file — DiagramsCode/

| File cũ (`DiagramsCode/`) | File mới (`DiagramsCode/`) | Ghi chú |
|--------------------------|---------------------------|---------|
| `hinh4.2.drawio` | `hinh4.1.2-so-do-goi-module.drawio` | tên cũ thiếu phần mô tả |
| `hinh4.3-may-trang-thai.drawio` | `hinh4.2.2-may-trang-thai.drawio` | |
| `hinh4.4-trinh-tu-trao-doi.drawio` | `hinh4.2.3-trinh-tu-trao-doi.drawio` | |
| `hinh4.5-so-do-lop-unity.drawio` | `hinh4.2.4-so-do-lop-unity.drawio` | |
| `hinh4.6-cau-truc-thu-muc-phien.drawio` | `hinh4.2.5-cau-truc-thu-muc-phien.drawio` | |
| `hinh4.7-bo-cuc-giao-dien.drawio` | `hinh4.2.6-bo-cuc-giao-dien.drawio` | |
| *(chưa có)* | `hinh4.2.1-so-do-lop-ban-do-unity.drawio` | **tạo mới** ✅ |
| *(chưa có)* | `hinh4.2.5-so-do-lop-traffic-server.drawio` | **tạo mới** ✅ |

> `hinh4.1` (kiến trúc chi tiết) không có file drawio → không cần đổi.

### 3d. Cập nhật đường dẫn trong tex sau khi đổi tên

Chỉ cần sửa `\includegraphics{Hinhve/hinh4.X-...}` trong `4_Ket_qua_thuc_nghiem.tex`
sang tên file mới theo bảng 3a. **Không đổi bất kỳ thứ gì khác** — label, ref, DoAn.tex
đều giữ nguyên.

---

## 4. Thứ tự thực hiện (đã cập nhật)

**Bước 0 — Đổi tên file trước (làm trước khi sửa nội dung):** ✅ XONG
1. ✅ Đổi tên 11 file PNG trong `BaoCao_DATN/Hinhve/` theo bảng 3a
2. ✅ Đổi tên 6 file drawio trong `DiagramsCode/` theo bảng 3b
3. ✅ Sửa các `\includegraphics` trong tex sang tên file mới
4. ✅ Biên dịch thử — PDF 68 trang, không lỗi tham chiếu hình

**Bước 1 — Cập nhật drawio hinh4.1.2 (sơ đồ module):** ✅ XONG (chờ export PNG)
- ✅ Thêm box `ROAD` (Dựng bản đồ 3D · RoadDataListener · Maker) vào khối Unity
- ✅ Thêm cạnh UNET → ROAD nhãn "road_data (một lần)"
- ✅ Cập nhật nhãn cạnh liên khung PY→UN: thêm "road_data (một lần)"
- ✅ Dịch TRAFFIC/VEH/UI/OPT xuống 70px, mở rộng khối Unity thêm 100px
- ✅ Cập nhật bảng `tab:unity-modules`: thêm hàng "Dựng bản đồ 3D (Road)"
- ✅ Mở rộng đoạn văn 4.1.3 phía Unity: thêm mô tả nhóm bản đồ
- ⏳ Export PNG → `BaoCao_DATN/Hinhve/hinh4.1.2-so-do-goi-module.png` (cần mở draw.io thủ công)

**Bước 2 — Vẽ các sơ đồ lớp mới:** ⏳ ĐANG LÀM

> File `hinh4.2.1-pipeline-dung-ban-do.drawio` đã tạo nhưng là sơ đồ luồng (flow),
> không phải sơ đồ lớp. Giữ lại để tham khảo nội bộ; **không dùng làm hình chính**.

**2a. Sơ đồ lớp module dựng bản đồ Unity** — `hinh4.2.1-so-do-lop-ban-do-unity.drawio` ✅ XONG
- ✅ Tạo drawio với 7 lớp: RoadDataListener, RoadData, RoadDataSO, EdgeMaker, JunctionMaker, CrossingMaker, BuildingMaker
- ✅ Thể hiện quan hệ: RDL writes→SO, RDL deserializes RoadData, 4 Maker reads→SO
- ⏳ Export PNG → `BaoCao_DATN/Hinhve/hinh4.2.1-so-do-lop-ban-do-unity.png` (cần mở draw.io thủ công)

**2b. Sơ đồ lớp/module traffic phía Python server** — `hinh4.2.5-so-do-lop-traffic-server.drawio` ✅ XONG
- ✅ Vẽ class TrafficerData, TrafficLightData, CrossingReader (có thuộc tính + phương thức)
- ✅ Vẽ module trafficer, unity_vehicle, trafficLight như component
- ✅ Thể hiện quan hệ: module tạo dataclass, dataclass to_dict()→TCP 5050
- ⏳ Export PNG → `BaoCao_DATN/Hinhve/hinh4.2.5-so-do-lop-traffic-server.png` (cần mở draw.io thủ công)

**Bước 3 — Viết lại nội dung tex:**
- Bổ sung 1 câu + hàng bảng vào 4.1.3 (mục 1b, 1c)
- Chèn tiểu mục 4.2.1 mới (pipeline bản đồ) vào đầu mục 4.2
- Cập nhật/viết lại các tiểu mục còn lại của 4.2 nếu cần reorder
- Thêm 2 bullet lớp Road vào 4.2.4 (lớp chủ đạo)

**Bước 4 — Biên dịch và kiểm tra toàn bộ.**

---

## 5. Rủi ro & lưu ý

| Vấn đề | Xử lý |
|--------|-------|
| LaTeX numbering | **Giữ nguyên** `\counterwithin{figure}{chapter}` — hình vẫn đánh số 4.1, 4.2,... trong PDF. Tên file chỉ phục vụ quản lý nội bộ. |
| Chương 5 đã có mô tả thuật toán EdgeMaker/JunctionMaker | Mục 4.2.1 chỉ mô tả *vai trò* lớp. Thêm `(chi tiết thuật toán xem Mục 5.x)` nếu chồng lặp. |
| Cổng gửi road_data | **Đã xác nhận: cổng 5050.** `RoadDataListener` kết nối 5050, gửi `"RoadDataRequest"`, nhận rồi đóng kết nối (`realtime_render.py:228`). |
| Subfigure 4.3.2 gồm 2 ảnh (a/b) | Tên file dùng hậu tố `a`/`b`; trong tex chúng nằm trong cùng `{figure}` environment với `\subfigure` — LaTeX tự đánh (a), (b). |
