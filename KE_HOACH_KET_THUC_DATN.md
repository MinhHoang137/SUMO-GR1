# Kế hoạch hoàn thành ĐATN

## Hạng mục 1 — Chương 5: 2 hình nháp (TikZ)

**Tình trạng hiện tại:**
- `fig:edge-ribbon`: "Dựng dải mặt đường bám đường gấp khúc và hiệu chỉnh tại khúc cua **(bản nháp)**"
- `fig:junction-prism`: "Tam giác hóa đa giác nút giao rồi đùn thành khối ba chiều **(bản nháp)**"
- Cả hai là đồ họa TikZ nhúng trực tiếp trong `BaoCao_DATN/Chuong/5_Giai_phap_dong_gop.tex`

**Có nên dùng app.diagrams.net không?**

| Tiêu chí | TikZ (hiện tại) | app.diagrams.net |
|---|---|---|
| Tích hợp LaTeX | Hoàn hảo (vector, font đồng nhất) | Cần export PNG/SVG, thêm bước |
| Độ chính xác hình học | Cao (tọa độ tường minh) | Trung bình (kéo thả) |
| Thời gian chỉnh sửa | Lâu nếu chưa quen TikZ | Nhanh hơn |

**Khuyến nghị:** Giữ TikZ nếu hình đã đúng về mặt kỹ thuật, chỉ cần chỉnh thẩm mỹ. Dùng app.diagrams.net nếu muốn thêm màu sắc/chú thích phức tạp — nhưng phải export PDF để giữ vector.

**Việc cần làm:**
- [ ] Xem lại 2 hình TikZ, quyết định tinh chỉnh tại chỗ hay vẽ lại bằng app.diagrams.net
- [ ] Nếu dùng draw.io: export PDF → thay bằng `\includegraphics`
- [ ] Bỏ nhãn **(bản nháp)** khỏi caption sau khi hoàn thiện

---

## Hạng mục 2 — Tài liệu tham khảo

**Tình trạng hiện tại:** `BaoCao_DATN/Danh_sach_tai_lieu_tham_khao.bib` chứa 7 mục từ template mẫu, không liên quan đề tài — cần thay toàn bộ.

**Nguồn chính cần thêm:**

| Nguồn | Loại | Gợi ý cite key |
|---|---|---|
| Krajzewicz et al. (2012) "Recent Development and Applications of SUMO - Simulation of Urban MObility" | inproceedings | `sumo2012` |
| Wegener et al. (2008) "TraCI: An Interface for Coupling Road Traffic and Network Simulators" | inproceedings | `traci2008` |
| Unity Technologies — Unity Manual / Scripting API | misc | `unity_manual` |
| OpenStreetMap contributors — openstreetmap.org | misc | `osm` |
| Eclipse SUMO — sumo.dlr.de | misc | `sumo_web` |

**Nguồn phụ có thể bổ sung:**

| Nguồn | Khái niệm liên quan |
|---|---|
| RFC 793 (1981) — Transmission Control Protocol | Giao thức TCP kết nối server–Unity |
| Python Software Foundation — docs.python.org | Ngôn ngữ triển khai server |
| Newtonsoft.Json — James Newton-King | Thư viện parse JSON phía Unity |

**Việc cần làm:**
- [ ] Xóa 7 mục template không liên quan trong `.bib`
- [ ] Thêm các mục trên với đầy đủ trường `title`, `author`, `year`, `url`/`journal`
- [ ] Kiểm tra `\cite{}` trong các chương dùng đúng key chưa
- [ ] Chạy BibTeX/biber, xác nhận không lỗi

---

## Hạng mục 3 — Phụ lục A: Hướng dẫn cài đặt và vận hành

**Tình trạng hiện tại:** `BaoCao_DATN/Chuong/Phu_luc_A.tex` chứa nội dung template — cần thay toàn bộ.

**Lý do:** Server viết bằng Python không biên dịch thành `.exe`, người dùng phải tự cài môi trường.

**Cấu trúc đề xuất:**

```
A.1  Yêu cầu phần cứng và phần mềm
     - Windows 10/11
     - Python 3.10+
     - SUMO (đặt SUMO_HOME)
     - Unity build (không cần Editor)

A.2  Cài đặt môi trường Python
     - pip install -r requirements.txt
     - Kiểm tra: python -c "import traci"

A.3  Cài đặt SUMO
     - Tải từ sumo.dlr.de, thêm vào PATH
     - Đặt biến môi trường SUMO_HOME

A.4  Khởi chạy hệ thống
     - Bước 1: Chạy Unity build (UnityBuild/...)
     - Bước 2: python HelloWorld/launcher.py
     - Chọn tab Maze hoặc OSM, cấu hình, nhấn Start

A.5  Xử lý sự cố thường gặp
     - Lỗi kết nối TCP: kiểm tra port 5050/5053/5054
     - SUMO không tìm thấy: kiểm tra SUMO_HOME và PATH
```

**Việc cần làm:**
- [ ] Xóa nội dung template trong `Phu_luc_A.tex`
- [ ] Viết nội dung theo cấu trúc trên
- [ ] Xem `HelloWorld/Server/` để liệt kê đủ gói pip cần thiết
- [ ] Thêm lệnh kiểm tra nhanh xác nhận cài thành công

---

---

## Hạng mục 4 — Đánh giá: có nên đổi tất cả PNG sang PDF không?

**Tổng số:** 26 file `.png` đang được dùng trong báo cáo. Chia làm 2 nhóm:

### Nhóm ảnh chụp màn hình — **NÊN GIỮ PNG**

| File | Mô tả |
|---|---|
| `hinh2.1-sumo-gui.png` | Screenshot SUMO GUI |
| `hinh4.2.7-bo-cuc-giao-dien.png` | Screenshot giao diện launcher |
| `hinh4.3.1-anh-goc-nhin-3d-tu-tren-cao.png` | Ảnh chụp cảnh 3D |
| `hinh4.3.2a-goc-nhin-cua-1-xe-tu-hanh-boi-may-chu.png` | Ảnh chụp góc nhìn xe |
| `hinh4.3.2b-goc-nhin-trong-xe.png` | Ảnh chụp góc nhìn trong xe |
| `hinh4.3.3-va-cham-gay-un-tac.png` | Ảnh chụp va chạm |

→ Ảnh chụp màn hình là raster theo bản chất, PDF không cải thiện chất lượng. Giữ PNG.

### Nhóm sơ đồ kỹ thuật — **NÊN ĐỔI SANG PDF nếu in mờ**

| File | Loại sơ đồ |
|---|---|
| `hinh3.1-kien-truc-tong-quat.png` | Kiến trúc tổng quát |
| `hinh3.2-control-loop.png` | Vòng lặp điều khiển |
| `hinh2.2-so-do-use-case-tong-quat.png` | Use case |
| `hinh2.3-usecase-A.png` | Use case |
| `hinh2.4-van-hanh-mo-phong.png` | Activity diagram |
| `hinh2.5-quansat-dieukhien.png` | Diagram |
| `hinh2.6-laixe.png` | Diagram |
| `hinh2.7-ketqua.png` | Diagram |
| `hinh2.8-chiemquyen.png` | Diagram |
| `hinh2.9-traquyen.png` | Diagram |
| `hinh4.1.1-thiet-ke-kien-truc-chi-tiet.png` | Kiến trúc chi tiết |
| `hinh4.1.2-so-do-goi-module.png` | Sơ đồ gói |
| `hinh4.2.1-so-do-lop-ban-do-unity.png` | Class diagram |
| `hinh4.2.2-may-trang-thai-1-phuong-tien.png` | State machine |
| `hinh4.2.3-trinh-tu-trao-doi.png` | Sequence diagram |
| `hinh4.2.4-so-do-lop-unity.png` | Class diagram |
| `hinh4.2.5-so-do-lop-traffic-server.png` | Class diagram |
| `hinh4.2.6-cau-truc-thu-muc-phien.png` | Cấu trúc thư mục |

**Nguyên tắc quyết định:**
- Nếu sơ đồ vẽ bằng draw.io / PlantUML / Visio → export lại sang PDF, thay `\includegraphics{...png}` bằng `{...pdf}`. Sắc nét hơn đáng kể khi in.
- Nếu PNG đã được xuất ở độ phân giải cao (≥ 300 DPI) và in thử trông ổn → có thể giữ, không bắt buộc đổi.
- **Kiểm tra nhanh:** compile PDF, zoom lên 200–300% vào chữ trong sơ đồ — nếu vỡ hạt thì cần đổi.

**Việc cần làm:**
- [ ] Compile PDF, xem thử từng sơ đồ ở chế độ zoom cao
- [ ] Với sơ đồ nào bị vỡ/mờ: mở file gốc trong draw.io → Export → PDF → đổi extension trong `.tex`
- [ ] Xóa các file PNG tương ứng sau khi đã có PDF (giữ gọn thư mục `Hinhve/`)

---

## Thứ tự thực hiện gợi ý

1. **Phụ lục A** — Độc lập, viết một lần
2. **Tài liệu tham khảo** — Thu thập link/thông tin, nhập vào `.bib`
3. **Hình PNG → PDF** — Compile thử, kiểm tra, đổi những cái cần
4. **Hình chương 5** — Quyết định TikZ hay draw.io, hoàn thiện, bỏ nhãn nháp
