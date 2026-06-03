---
name: osm-ped-route-validation
description: Vì sao route người đi bộ OSM hay lỗi "Disconnected walk" và cách scenario.py tự lọc
metadata:
  type: project
---

Trong pipeline OSM (`Server/osm/scenario.py`), route người đi bộ được nối theo **node-adjacency** mức-cạnh (`_parse_net`), KHÔNG đảm bảo người đi bộ băng qua junction được. Tại các cụm junction ghép (`--junctions.join`), vỉa hè bị chia thành nhiều walkingarea rời rạc, có cái là ngõ cụt (chỉ có connection đi vào, không có đi ra) → runtime SUMO báo "could not find route across junction" / "Disconnected walk" và **quit cả mô phỏng**. Mode 3D (`--osm.elevation`) làm phân mảnh nặng hơn 2D nên tỉ lệ trúng cao hơn (đo được ~3/20 seed trên net thật). Lỗi phụ thuộc seed.

**Why:** mỗi personFlow hỏng lặp lại ~120 lượt/giờ; một flow hỏng đủ làm sim dừng.

**How to apply:**
- duarouter **KHÔNG** bắt được lỗi này (router intermodal dễ tính hơn pedestrian model) — đừng dùng nó để validate. Validator đáng tin duy nhất là chạy chính `sumo` headless.
- `scenario.py::_prune_unroutable` đã tự xử: ghi bản 1-lượt (number=1, bỏ period/end), chạy `sumo --ignore-route-errors`, gom id flow hỏng từ log, gỡ khỏi `.rou.xml`. Gọi cuối `generate_routes`.
- Lớp an toàn runtime: `traci.start` ở `realtime_render.py` và `pre_render.py` đã thêm `--ignore-route-errors`.
