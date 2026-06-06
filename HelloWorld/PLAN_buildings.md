# Kế hoạch: Lấp khoảng trống OSM bằng khối vuông tượng trưng

## Phân tích khoảng trống

Bản đồ hiện có: đường (Edge), giao lộ (Junction), vạch bộ hành (Crossing) — phần còn lại là **ô đất trống** giữa các con đường (city blocks). Mục tiêu đặt hộp đơn giản vào đó.

---

## Lựa chọn chiến lược

**A) OSM building polygons (chuẩn nhất)**
- Server đọc file `.osm` → trích xuất polygon toà nhà thực (`building=*`)
- Gửi xuống Unity dưới dạng `BuildingData[]` trong `RoadData`
- Unity extrude polygon → mesh khối chính xác theo hình OSM

**B) City block fill — lưới ô (đơn giản, không cần OSM building tag)**
- Server (hoặc Unity) tạo lưới ô vuông bao phủ bounding box mạng đường
- Ô nào **không overlap** với đường/giao lộ → đặt khối vuông
- Kích thước ô = tham số (vd 10–20m)

**C) Convex hull của city block (trung bình)**
- Tìm vùng kín bao quanh bởi các cạnh đường → 1 mesh lấp đầy
- Phức tạp hơn vì cần polygon clipping

**Đề xuất: Hướng A + fallback B**
Lý do: OSM file đã có, server Python dễ trích xuất với `xml.etree`. Nếu không có dữ liệu building thực → B làm fallback cho khu vực trống.

---

## Các bước triển khai

### Bước 1 — Server: trích xuất building polygon từ OSM

**File mới:** `Server/map/building_extractor.py`

```python
# Đọc file .osm, lấy way có tag building=*
# Trả về list [[{x,y}, ...], ...]  # tọa độ SUMO
```

- Tích hợp vào `RoadData` JSON: thêm trường `"buildings": [BuildingData]`
- `BuildingData`: `{id, vertices: [{x,y}], height}` — `height` ngẫu nhiên hoặc từ tag `building:levels`

### Bước 2 — Data model Unity

**File mới:** `Traffic/Road/Building/BuildingData.cs` (tương tự `JunctionData.cs`)

```csharp
[Serializable]
public class BuildingData {
    public string id;
    public Coordinate[] vertices;
    public float height; // mặc định 10f nếu không có tag
}
```

Thêm `BuildingData[] buildings` vào `RoadData.cs` và `RoadDataSO`.

### Bước 3 — Unity mesh builder

**File mới:** `Traffic/Road/Building/Building.cs` (tương tự `Junction.cs`)

- `Create(BuildingData)`: nhận polygon vertices
- Extrude polygon lên cao `height` (top face + side walls)
- Dùng lại `EarClipTriangulateXZ` từ `Junction.cs` cho top face
- Fallback: nếu polygon < 3 điểm → đặt 1 cube `height × footprint`

**File mới:** `Traffic/Road/Building/BuildingMaker.cs` (tương tự `JunctionMaker.cs`)

### Bước 4 — Fallback lưới ô (Hướng B)

**File mới:** `Traffic/Road/Building/BuildingGridFiller.cs`

- Tính bounding box toàn bộ mạng đường từ `RoadDataSO`
- Tạo lưới ô `cellSize × cellSize`
- Với mỗi ô: `Physics.CheckBox` hoặc geometry overlap check — nếu trống → spawn khối
- Chạy sau `EdgeMaker/JunctionMaker` hoàn tất

### Bước 5 — Prefab & Material

- `Assets/Prefabs/Road/Building.prefab` — GameObject rỗng + `Building` script
- Material: màu xám nhạt (đủ phân biệt với đường)
- `MeshCollider` tùy chọn (có thể tắt để tối ưu)

### Bước 6 — Tích hợp scene

Trong `RealtimeScene` và `PreRenderScene`:
- Thêm `BuildingMaker` GameObject (subscribe `OnRoadDataLoaded` giống các Maker khác)
- Thứ tự chạy: **sau** `RoadTerrain.SculptRoutine` để buildings không bị terrain đè

---

## Thứ tự ưu tiên

| Bước | Việc | Độ phức tạp |
|------|------|------------|
| 1 | Server trích xuất building từ OSM | Thấp |
| 2 | `BuildingData.cs` + cập nhật `RoadData` | Thấp |
| 3 | `Building.cs` — mesh extrude | Trung bình |
| 4 | `BuildingMaker.cs` + scene setup | Thấp |
| 5 | Fallback grid filler | Trung bình |

---

## Câu hỏi cần chốt trước khi code

1. **Hướng nào?** A (OSM thực) / B (lưới tự sinh) / A+B (cả hai)?
2. **File OSM** server đang dùng có sẵn để parse không, hay map load từ nguồn khác?
3. **Chiều cao:** ngẫu nhiên (vd 5–30m) hay đồng đều?
4. **Collider:** cần không (ảnh hưởng perf nếu nhiều toà nhà)?
