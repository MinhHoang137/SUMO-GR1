# Kế hoạch tối ưu hóa luồng dữ liệu SUMO ↔ Unity

> Tài liệu phân tích hiện trạng luồng dữ liệu realtime và đề xuất tối ưu, xếp theo
> tỷ lệ **lợi ích / công sức**. Mục tiêu: giảm độ trễ end-to-end và CPU khi số xe lớn,
> không đổi giao thức ở mức phá vỡ tương thích trừ khi nêu rõ.

## 1. Sơ đồ luồng hiện tại

### Download (SUMO → Unity), mỗi `simulationStep`
1. `realtime_render.run_simulation` gọi `traci.simulationStep()`.
2. `read_trafficers(traci)` — duyệt **từng** xe/người, mỗi đối tượng gọi **nhiều** lệnh TraCI
   riêng lẻ (`getPosition3D`, `getSpeed`, `getAngle`, …). → mỗi lệnh là 1 round-trip TraCI.
3. Đóng gói `data = {"st", "tl", "tr":[...]}`, gắn `"ts"` (timestamp).
4. `network.send_data` → `json.dumps(data) + "<END>"`, cắt theo `BUFFER_SIZE` 128KB, `sendall`.
5. Unity `TrafficDataListener.ListenForData` (thread riêng) → `Network.ReadMessage` gom tới `<END>`.
6. So sánh `jsonContent != lastJson` (chống trùng) → `JsonConvert.DeserializeObject<TrafficDataList>`.
7. `UnityMainThreadDispatcher.Enqueue(closure)` → main thread chạy `ProcessData` (3 vòng duyệt + alloc list).
8. `FilterTransform` cull xe theo khoảng cách camera (`SetActive`).

### Upload (Unity → SUMO)
- Uploader gửi **batch** mọi xe client-owned trong 1 message (replace-latest). Server `process_vehicle_updates` mirror/freeze + reconcile `managed_ids`.

---

## 2. Các điểm nghẽn đã xác định (xếp theo ưu tiên)

### 🔴 P0 — `Network.ReadMessage` ở Unity: quét chuỗi O(n²) + mất dữ liệu khi gói dính nhau
[Network.cs](TestGR1.1/Assets/Scripts/Network/Network.cs#L30-L60)
- **O(n²):** mỗi chunk đọc xong gọi `fullMessage.ToString().Contains(endMarker)` — dựng lại
  toàn bộ chuỗi và quét từ đầu **mỗi vòng**. Payload càng lớn (nhiều xe) càng đắt theo bình phương.
- **Mất frame:** khác với `network.py` (giữ `_recv_buffers` phần dư), bản C# **cắt bỏ** mọi byte
  sau `<END>`. Khi TCP gộp 2 message vào 1 lần đọc, message thứ hai bị **vứt** → rớt frame realtime.
- **Alloc:** `new byte[bufferSize]` (128KB) + `StringBuilder.ToString()` mỗi vòng đọc.

**Đề xuất:** viết lại reader có **buffer bền per-connection** (giữ phần dư như `network.py`),
chỉ quét `<END>` trên **byte mới đọc** (theo dõi offset), tái dùng buffer. Tách khung (framing)
ở mức byte trước khi decode UTF-8.

### 🔴 P0 — `read_trafficers`: N×k round-trip TraCI mỗi step
[trafficer.py](Server/Traffic/trafficer.py#L27-L78)
- Với N xe, mỗi xe ~3–4 lệnh TraCI tuần tự → **N×k** round-trip qua socket TraCI. Đây là chi phí
  chi phối thời gian 1 vòng khi N lớn, làm `elapsed` ăn hết `time_step`.

**Đề xuất:** dùng **TraCI subscriptions**. Một lần `traci.vehicle.subscribe(id, [VAR_POSITION3D,
VAR_SPEED, VAR_ANGLE])` (và context subscription cho xe mới), rồi mỗi step chỉ
`traci.vehicle.getAllSubscriptionResults()` → **1** round-trip gom tất cả. Tương tự cho `person`.
Đây thường là cải thiện lớn nhất phía server.

### 🟠 P1 — Bật `TCP_NODELAY` (tắt Nagle) hai đầu
- Stream nhỏ, nhịp 50ms, cần độ trễ thấp. Nagle có thể gộp/giữ gói tới 40ms.

**Đề xuất:** `sock.setsockopt(IPPROTO_TCP, TCP_NODELAY, 1)` ở server; `client.NoDelay = true` ở Unity
(`TcpClient`). Rẻ, giảm jitter độ trễ ngay.

### 🟠 P1 — Nén payload JSON
- JSON text rất "phình". Snapshot vài trăm xe → hàng trăm KB/step. Băng thông & thời gian
  serialize/parse đều tốn.

**Đề xuất (tăng dần):**
1. **gzip/zlib** payload trước khi gửi (Python `zlib.compress`, Unity `GZipStream`/`DeflateStream`).
   JSON nén ~5–10×. Đánh đổi: chút CPU nén. Thường lời với mạng/USB-localhost lớn.
2. Hoặc **MessagePack** (binary) thay JSON — vừa nhỏ vừa parse nhanh, nhưng đổi giao thức cả 2 đầu.
3. Giữ làm tròn float 2 chữ số (đã có) — tốt.

### 🟠 P1 — Interest management / delta (chỉ gửi cái cần)
- Server stream **mọi** xe SUMO mỗi step, nhưng Unity `FilterTransform` **cull** xe xa camera ngay.
  → tốn băng thông + parse cho xe người chơi không thấy.

**Đề xuất:**
- **Area of Interest:** Unity gửi vị trí camera (kênh cmd 5054 đã có) → server chỉ stream xe trong
  bán kính R (+ vùng đệm). Giảm tải tuyến tính theo mật độ.
- **Delta encoding:** chỉ gửi xe có thay đổi đáng kể so với step trước (vị trí/heading vượt ngưỡng) +
  danh sách id rời đi. Phức tạp hơn, để sau AoI.

### 🟡 P2 — Vòng nhận của Unity: dedup & alloc
[TrafficDataListener.cs](TestGR1.1/Assets/Scripts/Traffic/TrafficDataListener.cs#L41-L86)
- `jsonContent != lastJson` giữ **bản sao chuỗi đầy đủ** và so sánh toàn chuỗi mỗi packet → alloc + CPU.
  Nếu đã làm framing tốt và server không gửi trùng, có thể bỏ hoặc thay bằng so hash.
- `DeserializeObject<TrafficDataList>` tạo `List` mới mỗi packet. Cân nhắc `JsonSerializer` tái dùng,
  hoặc parser thủ công ghi vào buffer tái dùng (pool) cho `tr`.
- `UnityMainThreadDispatcher.Enqueue(lambda)` bắt closure mỗi packet → GC. Cân nhắc hàng đợi
  struct/đối tượng tái dùng.

### 🟡 P2 — `ProcessData`: cấp phát & nhiều vòng duyệt
[TraffiicerManager.cs](TestGR1.1/Assets/Scripts/Traffic/Trafficer/TraffiicerManager.cs#L59-L119)
- `new List<Trafficer>(trafficerDict.Values)` mỗi packet (1 alloc/step). Duyệt 4 lần (mark, apply,
  despawn, recycle).

**Đề xuất:** tái dùng `List` thành viên (clear thay vì new); gộp vòng despawn vào vòng recycle.
Lợi ích nhỏ nhưng dễ làm, giảm GC spike.

### 🟡 P2 — Server dựng full chuỗi trong RAM rồi cắt
[network.py](Server/network.py#L57-L76)
- `json.dumps` toàn snapshot thành 1 chuỗi lớn rồi cắt lát — alloc lớn mỗi step. Chấp nhận được,
  nhưng nếu chuyển sang nén/binary thì xử lý luôn ở đây.

---

## 3. Lộ trình thực hiện theo giai đoạn

### Giai đoạn 1 — Sửa nhanh, rủi ro thấp, lợi ích cao ✅ ĐÃ LÀM
- [x] **P0** Viết lại `Network.ReadMessage` (buffer bền per-connection + quét marker incremental ở mức
      byte + giữ phần dư sau marker). *Sửa cả bug rớt frame khi gói TCP dính nhau; bỏ quét O(n²).*
- [x] **P1** Bật `TCP_NODELAY`: Unity `client.NoDelay=true` (`CreateTcpClient`); server `setsockopt` trên socket đã accept.
- [x] **P2** Tái dùng list snapshot trong `ProcessData` (clear+nạp lại thay vì `new` mỗi packet).
      *(`lastJson` giữ nguyên làm dedup an toàn — chi phí thấp, không đổi hành vi.)*

→ *Kỳ vọng: giảm CPU Unity rõ rệt khi đông xe, hết rớt frame, độ trễ ổn định hơn. Không đổi giao thức.*

### Giai đoạn 2 — Tối ưu server, vẫn giữ giao thức JSON ✅ ĐÃ LÀM
- [x] **P0** Chuyển `read_trafficers` (xe + người) sang **TraCI subscriptions**: subscribe mỗi đối tượng
      1 lần, mỗi step chỉ `getAllSubscriptionResults()` (1 round-trip) thay vì ~4N lệnh riêng lẻ.
      Tự đồng bộ tập subscribe (subscribe id mới, tỉa id đã rời); có fallback đọc trực tiếp nếu thiếu.
- [x] **Đã đo & kiểm chứng** (scenario HelloWorld, ~90 xe, 200 step, localhost):
      - Đúng đắn: 2763 phép đọc, **0 sai lệch** vị trí/tốc độ vs đọc trực tiếp, không thiếu xe.
      - Hiệu năng: đọc trực tiếp 3769ms → subscription **372ms** → **~10× nhanh hơn** (chênh tăng theo mật độ xe).

→ *Đạt: thời gian xử lý 1 step giảm mạnh; `elapsed` mỗi vòng nhỏ hơn nhiều → giữ được `time_step` nhỏ.*

### Giai đoạn 3 — Giảm khối lượng truyền (đổi giao thức, làm 2 đầu đồng bộ)
- [ ] **P1** Nén gzip/zlib payload download (kèm cờ để bật/tắt khi debug).
- [ ] **P1** Area-of-Interest theo camera (Unity gửi vị trí qua cổng cmd; server lọc bán kính).
- [ ] (Tùy chọn) Delta encoding nếu AoI chưa đủ.

→ *Kỳ vọng: băng thông giảm nhiều lần; parse phía Unity nhẹ hơn.*

### Giai đoạn 4 — Nâng cấp định dạng (lớn, cân nhắc sau)
- [ ] Cân nhắc MessagePack/binary thay JSON nếu vẫn nghẽn serialize/parse.

---

## 4. Đo lường & tiêu chí thành công
- **Sẵn có:** `"ts"`/`ServerTimeMs` → độ trễ end-to-end (`LatencyMs`), `LatencyText`. Dùng làm thước đo chính.
- Thêm log server: `elapsed` mỗi step (xử lý) và kích thước payload (bytes) trước/sau nén.
- Thêm đếm FPS / GC alloc Unity (Profiler) trước–sau mỗi giai đoạn.
- **Kịch bản benchmark cố định:** cùng `.map`, cùng số xe (vd 200/500/1000), cùng `time_step` → so sánh.

### Tiêu chí
| Hạng mục | Trước | Mục tiêu |
|---|---|---|
| Độ trễ end-to-end (N=500) | đo baseline | giảm ≥ 30% |
| `elapsed` xử lý/step server (N=500) | đo baseline | giảm ≥ 50% (sau subscriptions) |
| Rớt frame khi gói dính nhau | có | 0 |
| Kích thước payload/step | đo baseline | giảm ≥ 5× (sau nén/AoI) |

---

## 5. Rủi ro & lưu ý
- Đổi framing/nén/định dạng phải **đồng bộ cả 2 đầu** trong cùng commit, kèm cờ tương thích để
  fallback khi debug.
- TraCI subscriptions: nhớ `subscribe` cho xe **mới xuất hiện** và bỏ theo dõi xe đã rời (hoặc dùng
  context subscription) — tránh sót/lỗi.
- AoI tương tác với `FilterTransform` và với **xe client-owned** (xác xe/đang lái): xe client-owned
  KHÔNG được lọc bỏ dù xa camera — vòng đời của chúng do `existState` quyết, không do AoI server.
  Phải loại trừ tường minh.
- Giữ tương thích với **replay/pre-render** (`scenario_recorder`): nếu đổi định dạng payload realtime,
  kiểm tra `pre_render.py`/replay vẫn đọc được (hiện dùng cùng cấu trúc `data`).
- Việc nén/đổi định dạng cần kiểm cả đường **upload** (`unity_vehicle`/`VehicleSender`) nếu muốn nhất quán.

---

*Ưu tiên gợi ý bắt đầu:* **Giai đoạn 1 (P0 ReadMessage + NODELAY)** vì rủi ro thấp, sửa luôn bug
rớt frame; sau đó **Giai đoạn 2 (TraCI subscriptions)** cho cú nhảy hiệu năng server lớn nhất.
