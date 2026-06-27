# SUMO-GR1: Hệ thống mô phỏng giao thông tích hợp SUMO + Unity

Dự án tốt nghiệp (ĐATN) — Tích hợp trình mô phỏng giao thông đô thị **SUMO** với **Unity 3D** để trực quan hóa theo thời gian thực và hỗ trợ lái xe nhập vai (first-person driving).

---

## Tổng quan

Hệ thống gồm hai thành phần chính hoạt động song song:

- **Python Server** (`HelloWorld/Server/`): Chạy mô phỏng SUMO qua TraCI, phát dữ liệu giao thông qua TCP tới Unity.
- **Unity Client** (`HelloWorld/TestGR1.1/`): Nhận dữ liệu TCP, render 3D phương tiện/người đi bộ/đèn giao thông, cho phép người dùng điều khiển xe trong mô phỏng.

**Ba chế độ tạo bản đồ:**
| Chế độ | Mô tả |
|--------|-------|
| **OSM** | Import file bản đồ thực tế từ OpenStreetMap (`.osm`) |
| **Custom (Netedit)** | Dùng file mạng lưới tự vẽ từ SUMO Netedit (`.net.xml` + `.rou.xml`) |
| **Maze** | Tạo kịch bản từ file mê cung (`.map`) — dùng cho benchmark |

---

## Yêu cầu hệ thống

| Thành phần | Phiên bản |
|-----------|-----------|
| Python | 3.10+ |
| Unity | 6000.3.9f1 (Unity 6) |
| OS | Windows 10/11 |
| RAM | 8 GB+ |

> **Lưu ý:** SUMO được cài tự động qua package `eclipse-sumo` trong bước cài đặt. Không cần cài SUMO thủ công.

---

## Cài đặt

### Bước 1 — Clone repository

```bash
git clone https://github.com/<your-repo>/SUMO-GR1.git
cd SUMO-GR1/HelloWorld
```

### Bước 2 — Cài đặt môi trường Python

Chạy file cài đặt tự động (chỉ cần làm một lần):

```batch
install.bat
```

Script này sẽ:
1. Kiểm tra Python đã cài chưa
2. Tạo virtual environment `.venv`
3. Cài `eclipse-sumo` (bao gồm SUMO, TraCI, sumolib)
4. Cài Visual C++ Redistributable (runtime cho SUMO)
5. Kiểm tra import `traci` thành công

### Bước 3 — Mở Unity Project

1. Mở **Unity Hub**
2. Chọn **Add project from disk**
3. Trỏ đến thư mục `HelloWorld/TestGR1.1`
4. Mở project bằng **Unity 6000.3.9f1**

---

## Cách chạy

### 1. Khởi động Python Server (Launcher GUI)

```batch
cd HelloWorld
python launcher.py
```

Hoặc chạy nhanh:

```batch
Simulation.bat
```

Giao diện Launcher có 3 tab tương ứng 3 chế độ mô phỏng.

---

### 2. Chọn chế độ mô phỏng

#### Chế độ OSM (Tab 1) — Khuyến nghị cho người mới

1. Nhấn **"Chọn file OSM"** → chọn file `.osm` (ví dụ: `TestScript/TimesCity.osm`)
2. Chọn chế độ bản đồ: **2D** (phẳng) hoặc **3D** (có độ cao)
3. Cấu hình số nút giao, độ dài tuyến đường
4. Bật/tắt phương tiện và người đi bộ
5. Nhấn **"Khởi động Server"**

#### Chế độ Custom / Netedit (Tab 2)

1. Chọn thư mục chứa file `.net.xml` và `.rou.xml` tự vẽ từ SUMO Netedit
2. Chọn chế độ render: **Realtime** (TCP streaming) hoặc **Pre-render** (ghi file JSON rồi phát lại)
3. Nhấn **"Khởi động Server"**

#### Chế độ Maze (Tab 3) — Benchmark

1. Chọn file `.map` trong thư mục `Server/map/`
2. Cấu hình số làn đường, cặp OD, kiểu nút giao (CS/SS/IO/OI)
3. Nhấn **"Khởi động Server"**

---

### 3. Chạy Unity

Khi Python Server khởi động thành công, Unity được mở theo một trong hai cách:

#### Cách A — Dùng file build sẵn (khuyến nghị cho người dùng cuối)

Server tự động mở `HelloWorld/UnityBuild/TestGR1.1.exe` ngay khi khởi động. Không cần thao tác thêm.

> **Yêu cầu:** File `HelloWorld/UnityBuild/TestGR1.1.exe` phải tồn tại.  
> Nếu chưa có, xem [hướng dẫn build Unity](#build-unity-thành-exe) bên dưới.

#### Cách B — Chạy từ Unity Editor (dành cho developer)

Nếu muốn chỉnh sửa code C# và test trực tiếp:

1. Mở **Unity Hub** → **Add project from disk** → chọn `HelloWorld/TestGR1.1`
2. Mở bằng **Unity 6000.3.9f1**
3. Nhấn **Play** trong Editor — Unity sẽ tự kết nối tới server đang chạy

> Khi dùng Unity Editor, server vẫn tự mở exe nếu file tồn tại (dòng `subprocess.Popen` trong `Server/render/realtime_render.py`). Comment dòng đó lại để tránh hai client kết nối cùng lúc.

---

### Build Unity thành exe

Để tạo file `TestGR1.1.exe` cho Cách A:

1. Mở `HelloWorld/TestGR1.1` trong Unity Editor
2. Vào **File → Build Settings**
3. Chọn platform **Windows, Mac, Linux Standalone** → **Windows**
4. Nhấn **Build**, chọn thư mục output là `HelloWorld/UnityBuild/`
5. Đặt tên file là `TestGR1.1.exe`

---

---

### 4. Điều khiển trong Unity

| Thao tác | Phím / Chuột |
|---------|-------------|
| Di chuyển camera tự do | `W A S D` + kéo chuột phải |
| Bám theo xe | Click vào xe → camera tự động theo |
| Chiếm quyền điều khiển xe | Click vào xe → nhấn nút **"Chiếm quyền"** trên UI |
| Nhả quyền điều khiển | Nhấn nút **"Trả quyền"** trên UI |
| Lái xe (khi đang điều khiển) | `W A S D` hoặc phím mũi tên |

**Màu sắc phương tiện (hiển thị trong SUMO-GUI khi dùng chế độ 2D+3D):**
- Vàng: Xe do SUMO điều khiển tự động
- Đỏ: Xe của người chơi (CLIENT_CAR)
- Xanh dương: Xe server đang bị người chơi chiếm quyền

> Trong Unity 3D, xe người chơi (CLIENT_CAR) hiển thị màu đỏ; các xe còn lại có màu ngẫu nhiên.

---

## Cấu trúc thư mục

```
SUMO-GR1/
├── HelloWorld/
│   ├── launcher.py              # GUI launcher chính
│   ├── osm_launcher.py          # Công cụ build kịch bản từ OSM
│   ├── install.bat              # Cài đặt môi trường
│   ├── Simulation.bat           # Chạy nhanh
│   ├── requirements.txt
│   │
│   ├── Server/                  # Python backend
│   │   ├── main.py              # Điểm khởi chạy server
│   │   ├── render/
│   │   │   ├── realtime_render.py   # TCP streaming tới Unity
│   │   │   └── pre_render.py        # Ghi kịch bản ra JSON
│   │   ├── Traffic/             # Logic giao thông (đèn, xe, người đi bộ)
│   │   ├── osm/                 # Pipeline xử lý OSM → SUMO
│   │   ├── SUMO_xml/            # Tạo file mạng lưới và tuyến đường
│   │   ├── VRP/                 # Chế độ Vehicle Routing Problem
│   │   ├── map/                 # File mê cung mẫu (.map)
│   │   ├── result/              # Output kịch bản đã tạo
│   │   └── SUMO_xml/            # File .net.xml, .rou.xml, .sumocfg
│   │
│   ├── TestGR1.1/               # Unity 3D project
│   │   └── Assets/Scripts/
│   │       ├── Traffic/         # Agent, xe, đèn giao thông
│   │       ├── Simulation/      # TCP Listener/Sender
│   │       └── UI/              # Camera, takeover UI
│   │
│   └── TestScript/              # Kịch bản mẫu (TimesCity.osm)
│
└── README.md
```

---

## Luồng dữ liệu

```
SUMO (TraCI) ──► realtime_render.py ──► TCP JSON ──► Unity Listener
                                                           │
                                                    TrafficerManager
                                                    (cập nhật xe/người)
                                                           │
                                                    UnityVehicle (render)
                                                           │
                                              [Người chơi điều khiển xe]
                                                           │
                                              Unity Sender ──► TCP Upload
                                                           │
                                              unity_vehicle.py (server sync)
```

---

## Xử lý sự cố thường gặp

**Unity không kết nối được với server:**
- Đảm bảo Python server đã hiển thị thông báo "Server started" trước khi nhấn Play trong Unity
- Kiểm tra firewall không chặn cổng TCP (mặc định `5555`)

**SUMO không tìm thấy:**
- Chạy lại `install.bat` và kiểm tra bước "Verifying traci import"

**Hiệu năng thấp / giật lag:**
- Giảm số lượng phương tiện tối đa trong Launcher
- Dùng chế độ **Pre-render** thay vì **Realtime** để ghi sẵn rồi phát lại

**Unity báo lỗi script:**
- Mở đúng phiên bản Unity 6000.3.9f1 (xem trong Unity Hub)

---

## Công nghệ sử dụng

- [SUMO](https://sumo.dlr.de/) — Simulation of Urban Mobility
- [TraCI](https://sumo.dlr.de/docs/TraCI.html) — Traffic Control Interface (Python API)
- [Unity 6](https://unity.com/) — 3D visualization engine
- [OpenStreetMap](https://www.openstreetmap.org/) — Dữ liệu bản đồ thực tế
