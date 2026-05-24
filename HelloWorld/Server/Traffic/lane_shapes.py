"""Cache shape 3D của tất cả lane từ net.xml.

Dùng chung cho:
- trafficer.py: suy Z cho pedestrian (TraCI person không có getPosition3D).
- trafficLight.py: lấy Z tại điểm cuối lane để đặt đèn trên terrain (không absolute Y=5).

Cache module-level, lazy init — parse net.xml 1 lần ở lần gọi đầu.
"""

import math
import os
import xml.etree.ElementTree as ET


_NET_XML_PATH = os.path.join(os.path.dirname(__file__), '../SUMO_xml/HelloWorld.net.xml')
# Mỗi entry: list[(x, y, z, cum_dist_from_start)].
_CACHE: "dict[str, list[tuple[float, float, float, float]]] | None" = None


def _load() -> dict:
    cache: dict = {}
    if not os.path.exists(_NET_XML_PATH):
        return cache
    try:
        root = ET.parse(_NET_XML_PATH).getroot()
    except ET.ParseError:
        return cache
    for edge in root.findall('edge'):
        for lane in edge.findall('lane'):
            lane_id = lane.get('id')
            shape = lane.get('shape')
            if not lane_id or not shape:
                continue
            pts: list[tuple[float, float, float, float]] = []
            cum = 0.0
            prev_xy: tuple[float, float] | None = None
            for token in shape.strip().split(' '):
                parts = token.split(',')
                if len(parts) < 2:
                    continue
                try:
                    x = float(parts[0])
                    y = float(parts[1])
                    z = float(parts[2]) if len(parts) >= 3 else 0.0
                except ValueError:
                    continue
                if prev_xy is not None:
                    cum += math.hypot(x - prev_xy[0], y - prev_xy[1])
                pts.append((x, y, z, cum))
                prev_xy = (x, y)
            if pts:
                cache[lane_id] = pts
    return cache


def _ensure_loaded() -> dict:
    global _CACHE
    if _CACHE is None:
        _CACHE = _load()
    return _CACHE


def get_z_at_lane_pos(lane_id: str, lane_pos: float) -> float | None:
    """Nội suy Z dọc theo lane tại vị trí `lane_pos` (mét, tính từ đầu lane)."""
    pts = _ensure_loaded().get(lane_id)
    if not pts:
        return None
    if lane_pos <= pts[0][3]:
        return pts[0][2]
    if lane_pos >= pts[-1][3]:
        return pts[-1][2]
    for i in range(1, len(pts)):
        if lane_pos <= pts[i][3]:
            d0, d1 = pts[i - 1][3], pts[i][3]
            seg = d1 - d0
            if seg <= 1e-9:
                return pts[i][2]
            t = (lane_pos - d0) / seg
            return pts[i - 1][2] + t * (pts[i][2] - pts[i - 1][2])
    return pts[-1][2]


def get_lane_end_z(lane_id: str) -> float | None:
    """Trả về Z tại điểm cuối lane (vertex cuối cùng của shape)."""
    pts = _ensure_loaded().get(lane_id)
    if not pts:
        return None
    return pts[-1][2]
