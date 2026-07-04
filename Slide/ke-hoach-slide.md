# Kế hoạch tạo Slide bảo vệ ĐATN

## Thông tin chung

| Trường | Nội dung |
|---|---|
| Tên đề tài | Hiển thị giao thông trong không gian 3D từ dữ liệu mô phỏng SUMO |
| Sinh viên | Đặng Minh Hoàng — Hoang.DM225719@sis.hust.edu.vn |
| GVHD | ThS. Nguyễn Tiến Thành |
| Đơn vị | Khoa Kỹ thuật máy tính — ĐH Bách khoa Hà Nội |
| Thời gian | HÀ NỘI, 06/2026 |
| Template | HUST Beamer (blue, 16:9) — `Slide_HUST.tex` + `beamerthemeHUST.sty` |
| File đầu ra | `Slide/Slide_DATN.tex` |

## Phân bổ thời gian

| Hoạt động | Thời gian |
|---|---|
| Thuyết trình slide | ~10 phút |
| Demo sản phẩm live | ~5 phút |
| Hỏi đáp hội đồng | ~15 phút |
| **Tổng** | **30 phút** |

---

## Cấu trúc slide (~14 frame)

### 0. Mở đầu (2 frame)

| Frame | Nội dung | Thời gian |
|---|---|---|
| Trang bìa | `\husttitlepage` — tên đề tài, SV, GVHD | — |
| Mục lục | `\tableofcontents` — 4 phần chính | 30s |

---

### 1. Đặt vấn đề & Mục tiêu (3 frame, ~2 phút)

**Nguồn:** `Chuong/1_Gioi_thieu.tex`

| Frame | Nội dung |
|---|---|
| Vì sao cần mô phỏng giao thông | Thực nghiệm trực tiếp có rủi ro nhân mạng và biến số không kiểm soát được; môi trường biệt lập thì chi phí quá cao |
| Hạn chế của SUMO 2D | SUMO mạnh nhưng góc nhìn 2D chỉ dành cho người quản lý, không tái hiện được góc nhìn người lái hay trình bày cho người không chuyên |
| Mục tiêu | (1) Tự động dựng bản đồ 3D từ SUMO/OSM; (2) Cập nhật xe, đèn, người đi bộ theo thời gian thực; (3) Tương tác lái xe & xử lý va chạm; (4) Lưu & phát lại kịch bản. Công nghệ: SUMO → Python/TraCI → Unity |

---

### 2. Kiến trúc hệ thống (2 frame, ~2 phút)

**Nguồn:** `Chuong/3_Cong_nghe.tex`, `Chuong/4_Ket_qua_thuc_nghiem.tex` (Section 4.1)

| Frame | Nội dung |
|---|---|
| Pipeline tổng quan | Sơ đồ 3 tầng: SUMO mô phỏng → Python/TraCI đọc trạng thái & gửi TCP → Unity dựng cảnh & tương tác. Luồng ngược: vị trí xe người lái phản ánh về SUMO. Điểm mạnh: hai tầng tách biệt hoàn toàn, đổi kịch bản không cần sửa Unity |

---

### 3. Đóng góp kỹ thuật nổi bật (4 frame, ~4 phút)

**Nguồn:** `Chuong/5_Giai_phap_dong_gop.tex`

| Frame | Nội dung |
|---|---|
| Dựng bản đồ 3D chính xác | Thách thức: chuyển dữ liệu điểm tọa độ SUMO thành mesh đường và nút giao 3D đúng hình dạng, không bị méo tại khúc cua và nút phức tạp. Chi tiết thuật toán trong Chương 5 |
| Chiếm quyền & lái xe tương tác | Người dùng chiếm bất kỳ xe nào đang chạy → lái bằng vật lý. Xe SUMO xung quanh nhận biết và tránh xe người lái. Va chạm → xe bị tông dừng lại gây ùn ứ như thực tế |
| Lưu & phát lại kịch bản | Mọi lần chạy được tự động ghi toàn bộ diễn biến. Phát lại bất kỳ lần chạy nào mà không cần khởi động lại SUMO — thuận tiện cho phân tích và trình bày |
| Tối ưu hiệu năng | Tái sử dụng đối tượng (object pool), ẩn xe ngoài tầm nhìn camera, nội suy chuyển động để mượt dù SUMO chỉ cập nhật mỗi 0,1 giây |

---

### 4. Kết quả (2 frame, ~1,5 phút)

**Nguồn:** `Chuong/4_Ket_qua_thuc_nghiem.tex` (Section 4.4 & 4.5)

| Frame | Nội dung |
|---|---|
| Kiểm thử | 6 ca kiểm thử bao phủ các luồng chính → **tất cả đạt**. Hiện tượng duy nhất: lệch đồng bộ nhẹ khi tốc độ mô phỏng quá cao so với phần cứng |
| Đánh giá hiệu năng | Máy bàn (i5-14400F, RTX 4060): OSM **~120 FPS, 6.2ms**; mê cung 128×128 **100 FPS**. Laptop (i5-1240P, MX570): OSM **81.5 FPS** — ổn định trên phần cứng thông thường |

---

### 5. Kết luận (1 frame, ~30s → chuyển sang demo)

| Frame | Nội dung |
|---|---|
| Kết luận & hướng phát triển | Hệ thống tự động dựng cảnh từ bất kỳ kịch bản SUMO và cho phép người dùng tham gia vào dòng giao thông. Hướng phát triển: hoàn thiện tái nhập làn, hỗ trợ va chạm người-xe, đa người dùng, giao thức nhị phân, thêm loại phương tiện, hiệu ứng thời tiết, nâng cao đồ họa → hướng tới sản phẩm mô phỏng đô thị hoàn chỉnh |

---

### 6. Kết thúc (1 frame)

| Frame | Nội dung |
|---|---|
| Cảm ơn | `\hustthankyou` hoặc `\hustcontactpage` với GitHub: github.com/MinhHoang137/SUMO-GR1 |

---

## Tổng quan frame

| Phần | Frame | Thời gian |
|---|---|---|
| Mở đầu | 2 | — |
| 1. Đặt vấn đề & Mục tiêu | 3 | ~2 phút |
| 2. Kiến trúc hệ thống | 2 | ~2 phút |
| 3. Đóng góp kỹ thuật | 4 | ~4 phút |
| 4. Kết quả | 2 | ~1,5 phút |
| 5. Kết luận | 1 | ~30s |
| 6. Cảm ơn | 1 | — |
| **Tổng** | **15 frame** | **~10 phút** |

---

## Lưu ý kỹ thuật

- **Template:** Dùng lại `beamerthemeHUST.sty`, màu `[blue, 169]`
- **Ảnh minh họa:** Lấy từ `BaoCao_DATN/Hinhve/` — ưu tiên ảnh chụp màn hình Unity chạy thật
- **Sơ đồ pipeline:** Dùng TikZ hoặc ảnh từ báo cáo (`hinh3.1-kien-truc-tong-quat.png`)
- **Bảng số liệu FPS:** Dùng `tabular` trong `block` để nổi bật kết quả
- **Cột đôi:** `columns` environment — trái: mô tả, phải: hình/kết quả
- **Section slide:** Bật `\hustsectionpage{}` để tự chèn slide chuyển phần
- **Không cần công thức toán học** — chi tiết kỹ thuật để trong báo cáo

---

## Demo live (gợi ý kịch bản ~5 phút)

1. Khởi động Python server + SUMO + Unity (~1 phút)
2. Chạy bản đồ OSM thực tế → thấy bản đồ 3D tự động dựng (~1 phút)
3. Chiếm quyền một xe → lái thủ công, quan sát xe SUMO xung quanh phản ứng (~2 phút)
4. Gây va chạm → xem hệ thống xử lý xác xe gây ùn ứ (~30s)
5. Chuyển sang chế độ phát lại kịch bản đã lưu (~30s)

---

## Bước tiếp theo

1. [ ] Tạo file `Slide/Slide_DATN.tex` từ template `Slide_HUST.tex`
2. [ ] Điền nội dung từng frame theo cấu trúc trên
3. [ ] Chèn hình ảnh từ `BaoCao_DATN/Hinhve/` (kiểm tra tên file có sẵn)
4. [ ] Compile thử và chỉnh bố cục
5. [ ] Luyện thuyết trình — đảm bảo ≤10 phút để còn thời gian demo
