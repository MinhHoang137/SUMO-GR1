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

### 1b. Cập nhật bảng tab:unity-modules (trong tex)

Thêm một hàng vào `\begin{tabular}` ở mục 4.1.3:

```latex
Dựng bản đồ 3D (Road) & Nhận \texttt{road\_data.json} một lần khi khởi động;
dựng Mesh mặt đường, nút giao, vạch sang đường và công trình từ dữ liệu mạng. \\
```

**Vị trí chèn:** sau hàng "Mạng (Network)" vì pipeline bản đồ chạy ngay sau khi kết nối mạng.

### 1c. Bổ sung 1 câu vào đoạn văn mục 4.1.3

Tại đoạn mô tả phía Unity (hiện kết thúc ở "... cung cấp giao diện điều khiển và xử lý
tương tác lái xe"), thêm một câu trước hoặc sau câu kết:

> "Ngoài các nhóm trên, nhóm mô-đun \emph{Dựng bản đồ 3D} nhận dữ liệu mạng đường
> từ Python một lần khi khởi chạy và dựng lưới đa giác cho mặt đường, nút giao,
> vạch sang đường và công trình, tạo nên cảnh ba chiều nền cho toàn bộ phiên mô phỏng."

---

## 2. Thay đổi tại Mục 4.2 — Thiết kế chi tiết

**Nguyên tắc:** không xóa tiểu mục nào hiện có; chỉ **chèn thêm** một tiểu mục mới và
**cập nhật nhẹ** tiểu mục 4.2.3.

### 2a. Thêm tiểu mục mới: "Thiết kế pipeline dựng bản đồ 3D"

**Vị trí:** chèn làm tiểu mục đầu tiên của mục 4.2, trước "Máy trạng thái điều khiển
phương tiện". Lý do: bản đồ được dựng một lần ngay khi kết nối (trước khi xe xuất hiện),
nên về mặt logic nó xảy ra sớm nhất trong vòng đời phiên mô phỏng.

**Nội dung tiểu mục (khoảng 300–400 chữ + 1 sơ đồ pipeline):**

#### Phía Python — sinh `road_data.json`

Ngay sau khi SUMO khởi chạy và kết nối TraCI, server trích xuất dữ liệu mạng đường
thông qua các API của TraCI và thư viện phân tích `osmnx`/`sumolib`:

- **Junctions** (`traci.junction`): tọa độ các nút giao, hình dạng đa giác của mặt nút.
- **Edges** (`traci.edge`, `traci.lane`): danh sách làn đường với đa tuyến trung tâm,
  chiều rộng, số làn.
- **Crossings** (`crossing.py`): các vạch sang đường dành cho người đi bộ.
- **Buildings** (OSM/`sumolib`): đa giác nhà khi bản đồ nguồn là OpenStreetMap.

Dữ liệu được gom thành một gói JSON duy nhất và gửi qua cổng TCP 5050 **một lần** khi Unity
gửi yêu cầu `"RoadDataRequest"` (trước phiên mô phỏng chính). Không gửi lại trong suốt phiên.
Cùng lúc, gói này cũng được ghi vào `road_data.json` trong thư mục phiên để phục vụ phát lại.

#### Phía Unity — pipeline 4 Maker

Unity nhận gói qua `RoadDataListener`, lưu vào `RoadDataSO` (ScriptableObject dùng chung),
sau đó bốn lớp Maker đọc SO và dựng Mesh song song:

| Lớp | Đầu vào | Đầu ra |
|-----|---------|--------|
| `EdgeMaker` | Danh sách làn + đa tuyến trung tâm | Dải mặt đường (ribbon + miter) |
| `JunctionMaker` | Đa giác nút giao | Khối nút giao (triangulation → extrude) |
| `CrossingMaker` | Tọa độ vạch sang đường | Lưới vạch kẻ (quads) |
| `BuildingMaker` | Đa giác công trình + chiều cao | Khối nhà (prism) |

Mỗi Maker chạy một lần khi nhận SO, tạo `MeshFilter`/`MeshRenderer` cho từng đối tượng
và không cần cập nhật lại trong phiên (bản đồ tĩnh). Hình `\ref{fig:map-pipeline}` mô tả
luồng dữ liệu dựng bản đồ.

> **Phân biệt với Chương 5:** mục này mô tả *ai nhận gì, ai làm gì* (pipeline, phân chia
> trách nhiệm giữa các lớp). Chương 5 mô tả *làm thế nào* (thuật toán ribbon+miter,
> triangulation, prism). Không trùng lặp.

**Hình cần có:** `fig:map-pipeline` — sơ đồ flow đơn giản:

```
[Python: SUMO/TraCI/OSM]
        ↓ road_data.json (:5050, một lần)
[Unity: RoadDataListener]
        ↓ ghi vào
[RoadDataSO]
   ↙      ↓      ↘       ↘
EdgeMaker JunctionMaker CrossingMaker BuildingMaker
   ↓          ↓              ↓              ↓
Mesh đường  Mesh nút giao  Mesh vạch   Mesh nhà
```

File drawio: `DiagramsCode/hinh4.X-pipeline-dung-ban-do.drawio` (X = số hình tiếp theo
sau hinh4.2, cần điều chỉnh số hình cho phù hợp với thứ tự trong báo cáo).

---

### 2b. Cập nhật tiểu mục 4.2.3 — Thiết kế một số lớp chủ đạo

Hiện tại mục này chỉ liệt kê 6 lớp, tất cả thuộc phần mô phỏng/tương tác. Cần bổ sung
các lớp phía bản đồ:

Thêm vào danh sách `\begin{itemize}` (sau `SimulationSession`):

```latex
\item \texttt{RoadDataListener} (Unity): kết nối cổng 5050, gửi yêu cầu
\texttt{"RoadDataRequest"}, nhận gói dữ liệu mạng đường một lần, giải mã JSON
và ghi vào \texttt{RoadDataSO} rồi đóng kết nối.

\item \texttt{EdgeMaker}, \texttt{JunctionMaker}, \texttt{CrossingMaker},
\texttt{BuildingMaker} (Unity): bốn lớp dựng Mesh bản đồ 3D từ \texttt{RoadDataSO};
mỗi lớp chịu trách nhiệm một loại đối tượng địa lý và chạy một lần khi nhận SO.
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
| **4.2.1** | *(chưa có)* | `hinh4.2.1-pipeline-dung-ban-do.png` | **tạo mới** |
| **4.2.2** | `hinh4.3-may-trang-thai-1-phuong-tien.png` | `hinh4.2.2-may-trang-thai-1-phuong-tien.png` | đổi tên |
| **4.2.3** | `hinh4.4-trinh-tu-trao-doi.png` | `hinh4.2.3-trinh-tu-trao-doi.png` | đổi tên |
| **4.2.4** | `hinh4.5-so-do-lop-unity.png` | `hinh4.2.4-so-do-lop-unity.png` | đổi tên |
| **4.2.5** | `hinh4.6-cau-truc-thu-muc-phien.png` | `hinh4.2.5-cau-truc-thu-muc-phien.png` | đổi tên |
| **4.2.6** | `hinh4.7-bo-cuc-giao-dien.png` | `hinh4.2.6-bo-cuc-giao-dien.png` | đổi tên |
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
| *(chưa có)* | `hinh4.2.1-pipeline-dung-ban-do.drawio` | **tạo mới** |

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

**Bước 1 — Cập nhật drawio hinh4.1.2 (sơ đồ module):**
- Thêm box `ROAD` vào khối Unity
- Cập nhật nhãn cạnh liên khung PY→UN
- Export PNG → `BaoCao_DATN/Hinhve/hinh4.1.2-so-do-goi-module.png`

**Bước 2 — Vẽ mới drawio hinh4.2.1 (pipeline bản đồ):**
- Tạo `DiagramsCode/hinh4.2.1-pipeline-dung-ban-do.drawio`
- Export PNG → `BaoCao_DATN/Hinhve/hinh4.2.1-pipeline-dung-ban-do.png`

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
