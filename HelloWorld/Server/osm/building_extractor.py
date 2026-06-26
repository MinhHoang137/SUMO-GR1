"""Trích xuất polygon toà nhà (building=*) từ .osm → toạ độ mạng SUMO.

CHỈ dùng cho chế độ render bản đồ OSM. Map benchmark (sinh thủ tục từ .map qua
nod/edg/con) KHÔNG có dữ liệu building nên không gọi tới đây.

Phép chiếu lon/lat → (x, y) net dùng `polyconvert` (đi kèm SUMO, cùng chỗ với
netconvert mà dự án đã dùng). polyconvert tự áp đúng projParameter + netOffset của
net — KHÔNG cần pyproj (khác sumolib.convertLonLat2XY vốn đòi pyproj cho UTM).

Chiều cao không nằm trong .poly.xml nên được join lại từ tag OSM theo way id
(height / building:levels), thiếu thì bốc ngẫu nhiên (nhà dân).

Schema xuất (mỗi toà nhà):
    {"i": <way_id>, "h": <height_m>, "v": [{"x","y","z"}, ...]}   # z = cao độ nền (0)
khớp với BuildingData.cs phía Unity (Coordinate {x,y,z}).
"""

from __future__ import annotations

import os
import json
import random
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET

METERS_PER_LEVEL = 3.0      # quy đổi building:levels → mét
MIN_HEIGHT = 4.0
# Khi OSM KHÔNG có height / building:levels (đa số nhà dân) → bốc ngẫu nhiên trong khoảng.
# Seed theo way id nên cùng một toà nhà luôn ra cùng chiều cao qua các lần build.
RANDOM_HEIGHT_MIN = 6.0
RANDOM_HEIGHT_MAX = 24.0
MAX_VERTS = 64             # giảm đỉnh cho polygon quá phức tạp (toà nhà cong) → mesh nhẹ

_FALLBACK_TYPEMAP = (
    '<polygonTypes>\n'
    '    <polygonType id="building" name="building" color="1.0,.90,.90" layer="-1"/>\n'
    '</polygonTypes>\n'
)


def _parse_height(tags: dict) -> "float | None":
    """Ưu tiên tag 'height' (mét, có thể kèm đơn vị), rồi 'building:levels'."""
    raw = tags.get("height")
    if raw:
        try:
            return max(MIN_HEIGHT, float(str(raw).split()[0].replace(",", ".")))
        except ValueError:
            pass
    levels = tags.get("building:levels")
    if levels:
        try:
            return max(MIN_HEIGHT, float(str(levels).split()[0].replace(",", ".")) * METERS_PER_LEVEL)
        except ValueError:
            pass
    return None


def _random_height(way_id: str) -> float:
    """Chiều cao ngẫu nhiên ổn định (seed theo id) cho nhà dân không khai báo chiều cao."""
    rng = random.Random(way_id)
    return round(rng.uniform(RANDOM_HEIGHT_MIN, RANDOM_HEIGHT_MAX), 2)


def _find_typemap() -> "str | None":
    """Typemap OSM của SUMO (qua SUMO_HOME); None nếu không có (sẽ dùng fallback nội bộ)."""
    sumo_home = os.environ.get("SUMO_HOME")
    if sumo_home:
        cand = os.path.join(sumo_home, "data", "typemap", "osmPolyconvert.typ.xml")
        if os.path.exists(cand):
            return cand
    return None


def _osm_building_heights(osm_file: str) -> "dict[str, float | None]":
    """way id → chiều cao từ tag (None nếu way không khai báo height/levels)."""
    heights: "dict[str, float | None]" = {}
    root = ET.parse(osm_file).getroot()
    for way in root.findall("way"):
        wid = way.get("id")
        if not wid:
            continue
        tags = {t.get("k"): t.get("v") for t in way.findall("tag")}
        if "building" not in tags and "building:part" not in tags:
            continue
        heights[wid] = _parse_height(tags)
    return heights


def _parse_poly_shape(shape: str) -> "list[tuple[float, float]]":
    """'x,y x,y ...' (hoặc x,y,z) → list (x, y); bỏ đỉnh đóng vòng lặp lại."""
    verts: "list[tuple[float, float]]" = []
    for tok in shape.strip().split():
        parts = tok.split(",")
        if len(parts) < 2:
            continue
        try:
            verts.append((float(parts[0]), float(parts[1])))
        except ValueError:
            continue
    if len(verts) >= 2 and verts[0] == verts[-1]:
        verts = verts[:-1]
    return verts


def extract_buildings(osm_file: str, net_file: str) -> list:
    """Đọc .osm + .net.xml qua polyconvert, trả list dict building (toạ độ net). [] nếu lỗi."""
    if not os.path.exists(osm_file):
        print(f"[Building] Không tìm thấy .osm: {osm_file}")
        return []
    if not os.path.exists(net_file):
        print(f"[Building] Không tìm thấy .net.xml: {net_file}")
        return []
    if shutil.which("polyconvert") is None:
        print("[Building] Không thấy 'polyconvert' trong PATH (cần SUMO) — bỏ qua building.")
        return []

    typemap = _find_typemap()
    tmp_dir = tempfile.mkdtemp(prefix="bldg_")
    poly_path = os.path.join(tmp_dir, "buildings.poly.xml")
    if typemap is None:
        typemap = os.path.join(tmp_dir, "typemap.xml")
        with open(typemap, "w", encoding="utf-8") as f:
            f.write(_FALLBACK_TYPEMAP)

    try:
        cmd = [
            "polyconvert",
            "--osm-files", osm_file,
            "--net-file", net_file,
            "--type-file", typemap,
            "-o", poly_path,
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True,
                              encoding="utf-8", errors="replace")
        if proc.returncode != 0 or not os.path.exists(poly_path):
            print(f"[Building] polyconvert lỗi: {proc.stderr.strip() or proc.stdout.strip()}")
            return []

        heights = _osm_building_heights(osm_file)

        buildings = []
        skipped = 0
        root = ET.parse(poly_path).getroot()
        for poly in root.findall("poly"):
            ptype = poly.get("type") or ""
            if not ptype.startswith("building"):
                continue
            verts = _parse_poly_shape(poly.get("shape") or "")
            if len(verts) < 3:
                skipped += 1
                continue
            if len(verts) > MAX_VERTS:
                step = len(verts) / MAX_VERTS
                verts = [verts[int(i * step)] for i in range(MAX_VERTS)]

            pid = poly.get("id") or "0"
            height = heights.get(pid)            # None nếu không có tag (hoặc id là relation)
            if height is None:
                height = _random_height(pid)

            buildings.append({
                "i": pid,
                "h": round(height, 2),
                "v": [{"x": round(x, 3), "y": round(y, 3), "z": 0.0} for (x, y) in verts],
            })

        print(f"[Building] Trích {len(buildings)} toà nhà (bỏ {skipped} polygon thiếu đỉnh).")
        return buildings
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def write_buildings_json(osm_file: str, net_file: str, out_path: str) -> int:
    """Trích building và ghi JSON cạnh net. Trả về số toà nhà đã ghi."""
    buildings = extract_buildings(osm_file, net_file)
    out_dir = os.path.dirname(out_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(buildings, f, ensure_ascii=False, separators=(",", ":"))
    return len(buildings)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Trích building từ .osm → JSON toạ độ net SUMO")
    parser.add_argument("osm_file")
    parser.add_argument("net_file")
    parser.add_argument("-o", "--output", default="HelloWorld.buildings.json")
    args = parser.parse_args()

    n = write_buildings_json(args.osm_file, args.net_file, args.output)
    print(f"Đã ghi {n} toà nhà → {args.output}")
