# SUMO–Unity: Tính năng "Chiếm quyền điều khiển xe + va chạm sinh xác xe"

Tài liệu này bàn giao công việc đang dở (Chunk 4 & 5). Chunk 1–3 đã xong và commit.
Ngôn ngữ làm việc: tiếng Việt. Định danh code: tiếng Anh.

## Bối cảnh hệ thống

Hai luồng dữ liệu:
- **Download (SUMO→Unity):** `TrafficDataList` = `{"st": step, "tl": đèn, "tr": [TrafficerData]}`.
  `TrafficerData` chỉ có `i/t/sp/p/f` (KHÔNG có state). Server stream mọi xe SUMO mỗi bước.
- **Upload (Unity→SUMO):** `UnityVehicleData` = `i/p/f/sp/e` với `e` = `ExistState` (int).
  Gửi theo **batch** (cả danh sách xe client-owned) trong **1 message**, giữ batch mới nhất.

Mỗi prefab xe có: `Trafficer` + `Vehicle` (telemetry) + `UnityVehicle` + `WheelController` + `Rigidbody` + 4 `WheelCollider`.
Tất cả variant (`Vehicle Variant`, `Vehicle (1)/(2) Variant`, `UnityVehicle Variant`) đều là **Prefab Variant của `Vehicle.prefab`** nên kế thừa hết component.

### Máy trạng thái `ExistState` (`TestGR1.1/Assets/Scripts/Traffic/Trafficer/ExistState.cs`)
| State | Giá trị | Rigidbody | Ai lái (Unity) | SUMO | Vòng đời |
|-------|---------|-----------|----------------|------|----------|
| `Destroyed` | 0 | — | — | remove | recycle |
| `ServerControlled` | 1 | kinematic | `Trafficer.Move()` nội suy | tự lái | theo server |
| `ClientControlled` | 2 | dynamic | người chơi (physics) | mirror `moveToXY` | tới khi thả |
| `Wrecked` | 3 | dynamic | không ai | đông cứng `setSpeed 0` (ùn ứ) | despawn sau N bước → Destroyed |

Khóa điều khiển = **`existState`**, KHÔNG dựa vào sự hiện diện component.
- `Trafficer.IsClientOwned` = `ClientControlled || Wrecked` → gate bỏ qua trong `ProcessData`.
- `Trafficer.isStandaloneClient` = xe người chơi tự sinh (`CLIENT_CAR`), không bao giờ bị server chiếm / re-anchor.

## Đã xong (Chunk 1–3)

- **Chunk 1:** enum `Wrecked`; field `"st"` (step SUMO) trong payload download; `TrafficerManager.CurrentStep`.
- **Chunk 2:** `UnityVehicle.TakeControl/ReleaseControl/BecomeWreck` + `ApplyMode` (toggle kinematic + wheel colliders, hybrid);
  gate `ProcessData` theo `existState`; xe `CLIENT_CAR`; tách `WheelController` (component độc lập: `Drive/Steer/Brake/UpdatePoses/SetCollidersEnabled`).
- **Chunk 3:** `VehicleTakeoverUI` (nút chiếm/trả quyền); uploader gửi **batch** mọi xe client-owned;
  server nhánh `state 2` (mirror) + `state 3` (freeze); **reconcile** `managed_ids` (xe vắng khỏi batch → remove);
  màu sumo-gui: **vàng** = mặc định, **đỏ** = CLIENT_CAR, **xanh lam** = xe server bị chiếm.
- **Sửa kèm:** sinh CLIENT_CAR trên lane generic ngẫu nhiên (segment đầu > 5m, cách điểm đầu 5m, quay theo lane);
  `time_step` (sleep giữa các bước) do Unity điều khiển runtime; bug `CameraController.SetFreeToggle` bắn 2 sự kiện;
  pause cho `PedestrianVisual` (tránh "đi tại chỗ").

### File quan trọng
Unity:
- `Trafficer.cs` — existState, IsClientOwned, isStandaloneClient, seenThisFrame; `Move()` chỉ chạy khi ServerControlled; `OnEnable`/`Show` KHÔNG snap về destination nếu IsClientOwned (chống teleport khi cull).
- `Vehicle/UnityVehicle/UnityVehicle.cs` — TakeControl/ReleaseControl/BecomeWreck, ApplyMode, FixedUpdate (pause + drive), GetUnityVehicleData (tốc độ thật từ rb.linearVelocity).
- `Vehicle/WheelController.cs` — thao tác 4 bánh.
- `TraffiicerManager.cs` — ProcessData (gate IsClientOwned, recycle/pool theo isStandaloneClient), `CurrentStep`.
- `Vehicle/UnityVehicle/UnityVehicleManager.cs` — sinh CLIENT_CAR, uploader batch (`SendVehicleDataRoutine`).
- `Vehicle/UnityVehicle/VehicleSender.cs` — `SendBatch` (replace-latest, buffer 128KB).
- `UI/VehicleTakeoverUI.cs` — nút.
- `Traffic/TrafficDataList.cs` (Step), `Traffic/TrafficDataListener.cs` (set CurrentStep).

Server:
- `Server/Traffic/unity_vehicle.py` — `process_vehicle_updates`: nhánh state 0/2/3, reconcile `managed_ids`, set màu.
- `Server/render/realtime_render.py` — `"st"` trong payload, vòng lặp có pause (`pause_event`).

---

## CHUNK 4 — Va chạm → Wrecked + despawn

**Mục tiêu:** xe client (đang lái / xác xe) tông một xe `ServerControlled` → xe bị tông thành `Wrecked`
(physics, SUMO `setSpeed 0` gây ùn ứ); tự biến mất sau **N bước SUMO** kể từ cú tông đầu.

### Các bước
1. **Phát hiện va chạm** — thêm `OnCollisionEnter` vào `UnityVehicle` (hoặc component nhỏ riêng).
   Khi một xe **dynamic** (ClientControlled/Wrecked) đụng một xe **ServerControlled**:
   - Xe bị tông (ServerControlled) → `BecomeWreck()`.
   - Va chạm bắn trên CẢ hai object → phải xác định đúng xe ServerControlled để wreck (xe kia giữ nguyên).
   - **Bẫy:** xe bị tông đang **kinematic** → cần `BecomeWreck` lật sang dynamic ngay trong handler để physics đẩy được (trễ ~1 frame).
   - **Bẫy:** muốn xác xe văng thực tế → cân nhắc `rb.AddForce`/đặt `rb.linearVelocity` theo xung lực của xe tông trong `BecomeWreck`.

2. **`BecomeWreck` bổ sung** — thêm `public int wreckStartStep;` đặt `= TrafficerManager.Instance.CurrentStep` khi wreck.
   (Hiện `BecomeWreck` đã set state Wrecked + ApplyMode dynamic.)

3. **Despawn — ĐẾM TẬP TRUNG (quan trọng, chống cull):** trong `TrafficerManager.ProcessData` (hoặc 1 tick trung tâm),
   duyệt trafficer; với xe `Wrecked`: nếu `CurrentStep - wreckStartStep >= N` → set `existState = Destroyed`
   (→ vòng 3 recycle; biến mất khỏi batch upload → server reconcile xoá khỏi SUMO).
   - **N** = số bước SUMO tồn tại của xác xe. Để thành `const`/`SerializeField` (giá trị do người dùng chốt, vd 100–200).
   - Phải đếm tập trung vì xác xe có thể bị `FilterTransform` cull (`SetActive(false)`) → bộ đếm trên chính GameObject sẽ đứng → rò rỉ. `ProcessData` chạy mỗi packet server, không phụ thuộc xe active.
   - Pause: `CurrentStep` đứng yên khi server pause → despawn tự dừng. OK.

4. **Nhánh "xe đang lái bị tông"** — khi xe `ClientControlled` của người chơi dính va chạm → latch cờ `hasCrashed = true`.
   Trong `ReleaseControl`: nếu `hasCrashed` → gọi `BecomeWreck()` thay vì trả về server (re-anchor ở chunk 5).
   (Đường gọi `ReleaseControl`: nút trả quyền + camera rời xe trong `VehicleTakeoverUI`.)

5. **Server** đã có nhánh `state 3` (freeze) + reconcile remove. CẦN KIỂM: SUMO có cơ chế **teleport xe kẹt**
   (`--time-to-teleport`, mặc định ~300s) — nếu N lớn, SUMO có thể tự teleport xác xe sớm. Cân nhắc đặt `--time-to-teleport -1`
   hoặc dùng `traci.vehicle.setStop(...)` thay `setSpeed(0)`.

6. **Upload:** xác xe là IsClientOwned → uploader đã đưa vào batch (state 3) → server freeze. Khi Destroyed → vắng batch → reconcile remove. Không cần kênh xoá riêng.

### Bẫy va chạm cần kiểm trong Unity
- Xe SUMO khác là transform kinematic — không phản ứng vật lý cho tới khi bị wreck. Player tông xe server: xe server kinematic → player nảy ra; `OnCollisionEnter` lật xe server sang Wrecked (dynamic) để bị đẩy.
- Thân xe phải có **Collider (convex) + Rigidbody** để bắn `OnCollisionEnter` (WheelCollider tách riêng, không tính). Kiểm prefab.
- Ma trận va chạm (Layer Collision Matrix): bảo đảm xe va chạm được với nhau.

---

## CHUNK 5 — Trả quyền & re-anchor (xe tự chạy lại)

**Mục tiêu:** người chơi thả một xe server đã chiếm (KHÔNG bị tông) → SUMO snap xe về lane gần nhất, cấp route, bật lại autopilot.
Nếu đi quá xa lane (không snap được) → hủy xe.

**Hiện trạng (chunk 3):** thả quyền chỉ set `ServerControlled` → uploader ngừng gửi → reconcile **REMOVE** khỏi SUMO (tạm).
Chunk 5 thay "remove khi thả" bằng "re-anchor".

**Vấn đề:** reconcile "vắng → remove" không phân biệt *thả* (re-anchor) với *huỷ* (remove). Cần tín hiệu thả.

### Các bước
1. **Tín hiệu thả:** khi `ReleaseControl` (không crashed) → gửi **một** message upload với `state = 1` (ServerControlled) cho xe đó
   TRƯỚC khi nó rời batch. Uploader hiện chỉ gửi xe IsClientOwned; `ServerControlled` không nằm trong đó →
   cần cơ chế one-shot: ví dụ `List<string> pendingReleaseIds` mà uploader drain 1 lần, gửi `{id, state=1, pos, forward}`.

2. **Server: nhánh `state == 1` (re-anchor), CHẠY 1 LẦN:**
   - `edge, lanePos, laneIdx = traci.simulation.convertRoad(x, y, vClass="passenger")`
   - Nếu `convertRoad` rỗng HOẶC khoảng cách snap > `SNAP_THRESHOLD` (biến riêng, mặc định **20m**) → không re-anchor được → set xe `Destroyed` (remove khỏi SUMO + Unity recycle).
   - Ngược lại: `traci.vehicle.moveTo(veh_id, f"{edge}_{laneIdx}", lanePos)` (hoặc `moveToXY` keepRoute=2 để map vào lane).
   - Cấp route mới: `traci.vehicle.changeTarget(veh_id, <edge_đích>)` hoặc `rerouteTraveltime(veh_id)`.
   - Trả lái cho SUMO: `setSpeedMode(veh_id, 31)`, `setLaneChangeMode(veh_id, <default ~1621>)`, `setSpeed(veh_id, -1)`.
   - `setColor(veh_id, vàng)` để bỏ màu xanh chiếm quyền.
   - Bỏ `veh_id` khỏi `managed_ids` (để reconcile KHÔNG xoá nó; giờ nó là xe server bình thường).
   - `SNAP_THRESHOLD` tách thành biến (yêu cầu của người dùng).

3. **Tương tác reconcile:** xe re-anchor phải được gỡ khỏi `managed_ids` → reconcile không đụng. Sau đó Unity ngừng upload nó (ServerControlled) → vắng batch nhưng không còn trong managed_ids → an toàn.

4. **Unity sau khi thả + re-anchor:** `existState = ServerControlled` → `ProcessData` nối lại `Set()` (nội suy) khi SUMO stream xuống.
   SUMO chưa remove xe (vẫn stream) nên xe Unity snap/lerp về vị trí re-anchor — chấp nhận "kéo" nhẹ hoặc lerp mượt.
   - Bẫy: vài frame giữa lúc gửi tín hiệu thả và lúc server xử lý, xe Unity là ServerControlled nhưng SUMO còn ở vị trí moveToXY cũ (setSpeedMode 0). Lệch nhẹ tạm thời. Nhỏ.
   - Bẫy: `ProcessData` recycle xe ServerControlled không thấy trong download. Nhưng SUMO vẫn stream xe re-anchor (chưa remove) → vẫn "seen". OK.

## Quyết định đã chốt
- Despawn theo **N bước SUMO** (không phải giây), đếm qua `"st"`/`CurrentStep`, **tập trung** trong ProcessData.
- Ngưỡng snap re-anchor = **biến riêng**, mặc định 20m; vượt → hủy xe.
- `CLIENT_CAR`: id `"CLIENT_CAR"`, màu đỏ, không re-anchor.
- Xe server bị chiếm: màu xanh lam. Re-anchor xong: trả về vàng.
- Hybrid: chỉ bật vật lý (dynamic + wheel collider) ở chế độ client/wreck (đã làm ở chunk 2).

## Cần người dùng chốt khi vào chunk 4
- **N** (số bước xác xe tồn tại): ví dụ 100–200?

## Chạy / test
- Server: `python launcher.py` (GUI) hoặc `Server/main.py` trực tiếp; chọn Realtime + Run with GUI.
- Sau khi sửa C#: mở Unity (Editor 6000.3.9f1) cho compile, xem Console sạch.
- Sửa Python: `python -m py_compile <file>` để check cú pháp nhanh.
- Test chunk 4: chiếm 1 xe (hoặc CLIENT_CAR) → tông xe server → xe bị tông chuyển xác (đông cứng trong sumo-gui, các xe sau dồn lại) → sau N bước biến mất.
- Test chunk 5: chiếm xe server (xanh lam) → lái đi → thả (camera rời / nút) → xe snap về lane, đổi lại vàng, chạy tiếp; lái ra xa rồi thả → xe bị hủy.
