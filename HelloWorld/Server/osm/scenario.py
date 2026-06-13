"""OSM scenario builder.

Pipeline:
    1. Chuyển .osm → .net.xml qua netconvert (2D hoặc 3D).
    2. Đọc .net.xml: chọn ngẫu nhiên N junction (lấy tối đa khả dụng nếu thiếu).
    3. Với mỗi junction, kiểm tra có thể đi ra cho xe / người đi bộ không;
       nếu có, sinh chuỗi K edge nối liền nhau theo thuật toán:
         - "random": random-walk K bước (cho phép lặp cạnh khi cần).
         - "max":    DFS không lặp cạnh, lấy chuỗi dài nhất ≤ K.
    4. Ghi .rou.xml (<flow><route edges>... và <personFlow><walk edges>...).
    5. Ghi .sumocfg trỏ tới cặp .net.xml + .rou.xml vừa tạo.
"""

from __future__ import annotations

import os
import sys
import re
import shutil
import random
import subprocess
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Tuple

_CUR_DIR = os.path.dirname(os.path.abspath(__file__))
_SERVER_DIR = os.path.abspath(os.path.join(_CUR_DIR, os.pardir))
if _SERVER_DIR not in sys.path:
    sys.path.insert(0, _SERVER_DIR)

from osm.osm_to_net import convert_osm_to_net_3d_roads  # noqa: E402


_SKIP_JUNCTION_TYPES = {"internal", "dead_end"}


# ─────────────────────────────────────────────────────────────────────────────
# Net parsing
# ─────────────────────────────────────────────────────────────────────────────

def _lane_allows(lane: ET.Element, vclass: str) -> bool:
    allow = (lane.get("allow") or "").strip()
    disallow = (lane.get("disallow") or "").strip()
    if allow:
        return vclass in allow.split()
    if disallow:
        return vclass not in disallow.split()
    return True


def _edge_allows(edge: ET.Element, vclass: str) -> bool:
    for lane in edge.findall("lane"):
        if _lane_allows(lane, vclass):
            return True
    return False


# adjacency value: (to_node, edge_id, allows_car, allows_ped)
AdjEntry = Tuple[str, str, bool, bool]
Adj = Dict[str, List[AdjEntry]]


def _parse_net(net_path: str) -> Tuple[List[str], Adj]:
    tree = ET.parse(net_path)
    root = tree.getroot()

    junctions: List[str] = []
    for junc in root.findall("junction"):
        jid = junc.get("id", "")
        jtype = junc.get("type", "")
        if not jid or jid.startswith(":") or jtype in _SKIP_JUNCTION_TYPES:
            continue
        junctions.append(jid)

    adj: Adj = {j: [] for j in junctions}
    for edge in root.findall("edge"):
        eid = edge.get("id", "")
        if eid.startswith(":"):
            continue
        u = edge.get("from")
        v = edge.get("to")
        if not u or not v or u not in adj:
            continue
        a_car = _edge_allows(edge, "passenger")
        a_ped = _edge_allows(edge, "pedestrian")
        adj[u].append((v, eid, a_car, a_ped))
    return junctions, adj


# ─────────────────────────────────────────────────────────────────────────────
# Walk strategies
# ─────────────────────────────────────────────────────────────────────────────

def _filter_options(adj: Adj, node: str, vclass: str) -> List[Tuple[str, str]]:
    out = adj.get(node, [])
    if vclass == "car":
        return [(nxt, eid) for (nxt, eid, ac, _ap) in out if ac]
    return [(nxt, eid) for (nxt, eid, _ac, ap) in out if ap]


def _random_walk(adj: Adj, start: str, k: int, vclass: str) -> List[str]:
    """Chọn độ dài mục tiêu ngẫu nhiên trong [1, K], rồi random-walk tới khi đủ
    hoặc gặp dead-end. Không cho phép quay đầu (U-turn) — bỏ edge dẫn về junction
    vừa rời để tránh route như 'X -X' mà SUMO không có connection."""
    if k <= 0:
        return []
    target = random.randint(1, k)
    edges: List[str] = []
    cur = start
    prev: Optional[str] = None
    for _ in range(target):
        opts = _filter_options(adj, cur, vclass)
        if prev is not None:
            opts = [(nxt, eid) for (nxt, eid) in opts if nxt != prev]
        if not opts:
            break
        nxt, eid = random.choice(opts)
        edges.append(eid)
        prev = cur
        cur = nxt
    return edges


def _max_walk(adj: Adj, start: str, k: int, vclass: str) -> List[str]:
    """Cố gắng tìm walk đúng K cạnh, DFS không lặp cạnh và không quay đầu
    (không đi sang edge dẫn về junction trước đó); nếu không đủ K thì trả về
    walk dài nhất tìm được."""
    best: List[str] = []
    used: set = set()

    def dfs(node: str, prev: Optional[str], path: List[str]) -> None:
        nonlocal best
        if len(path) > len(best):
            best = path[:]
        if len(path) >= k:
            return
        opts = _filter_options(adj, node, vclass)
        if prev is not None:
            opts = [(nxt, eid) for (nxt, eid) in opts if nxt != prev]
        random.shuffle(opts)
        for nxt, eid in opts:
            if eid in used:
                continue
            used.add(eid)
            path.append(eid)
            dfs(nxt, node, path)
            path.pop()
            used.discard(eid)

    dfs(start, None, [])
    return best


_WALK_FNS = {
    "random": _random_walk,
    "max": _max_walk,
}


# ─────────────────────────────────────────────────────────────────────────────
# Route generation
# ─────────────────────────────────────────────────────────────────────────────

def generate_routes(net_path: str,
                    rou_path: str,
                    num_junctions: int,
                    edges_per_route: int,
                    algorithm: str = "random",
                    gen_car: bool = True,
                    gen_ped: bool = True,
                    ped_impatience: float = 0.5,
                    car_period: float = 30.0,
                    ped_period: float = 30.0,
                    begin: float = 0.0,
                    end_time: float = 3600.0,
                    seed: Optional[int] = None) -> bool:
    if seed is not None:
        random.seed(seed)

    junctions, adj = _parse_net(net_path)
    if not junctions:
        print("[Lỗi] Không tìm thấy junction nào trong .net.xml")
        return False

    n = min(int(num_junctions), len(junctions))
    if n <= 0:
        print("[Lỗi] num_junctions phải > 0.")
        return False
    chosen = random.sample(junctions, n)
    if n < int(num_junctions):
        print(f"[Info] Yêu cầu {num_junctions} junction nhưng chỉ có {len(junctions)} khả dụng — dùng {n}.")
    else:
        print(f"[Info] Đã chọn {n}/{len(junctions)} junction.")

    walk_fn = _WALK_FNS.get(algorithm, _random_walk)
    k = max(1, int(edges_per_route))

    routes_root = ET.Element("routes", {
        "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
        "xsi:noNamespaceSchemaLocation": "http://sumo.dlr.de/xsd/routes_file.xsd",
    })

    if gen_car:
        ET.SubElement(routes_root, "vType", {"id": "car", "vClass": "passenger"})

    vtype_ped = None
    if gen_ped:
        imp = max(0.0, min(1.0, float(ped_impatience)))
        vtype_ped = f"ped_{imp:.2f}".replace(".", "_")
        ET.SubElement(routes_root, "vType", {
            "id": vtype_ped, "vClass": "pedestrian", "impatience": f"{imp:.2f}",
        })

    car_count = 0
    ped_count = 0
    for idx, start in enumerate(chosen):
        if gen_car:
            edges = walk_fn(adj, start, k, "car")
            if edges:
                flow = ET.SubElement(routes_root, "flow", {
                    "id": f"f_{idx}",
                    "type": "car",
                    "begin": f"{begin:.2f}",
                    "end": f"{end_time:.2f}",
                    "period": f"{car_period:.2f}",
                    "departLane": "best",
                    "departSpeed": "max",
                })
                ET.SubElement(flow, "route", {"edges": " ".join(edges)})
                car_count += 1
        if gen_ped:
            edges = walk_fn(adj, start, k, "ped")
            if edges:
                pf = ET.SubElement(routes_root, "personFlow", {
                    "id": f"pf_{idx}",
                    "type": vtype_ped,
                    "begin": f"{begin:.2f}",
                    "end": f"{end_time:.2f}",
                    "period": f"{ped_period:.2f}",
                })
                ET.SubElement(pf, "walk", {"edges": " ".join(edges)})
                ped_count += 1

    tree = ET.ElementTree(routes_root)
    if hasattr(ET, "indent"):
        ET.indent(tree, space="    ", level=0)
    out_dir = os.path.dirname(rou_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    tree.write(rou_path, encoding="UTF-8", xml_declaration=True)
    print(f"[Thành công] Đã sinh {car_count} car flow + {ped_count} pedestrian flow → {rou_path}")

    # Lọc các flow không route được (vd vỉa hè cụm junction bị ngắt → "Disconnected walk").
    # Adjacency mức-cạnh không đảm bảo người đi bộ băng qua được junction, nên xác thực bằng
    # chính SUMO rồi gỡ flow hỏng — tránh mô phỏng quit lúc chạy thật.
    removed = _prune_unroutable(net_path, rou_path)
    if removed:
        print(f"[Info] Đã gỡ {len(removed)} flow không route được: {', '.join(sorted(removed))}")

    return (car_count + ped_count) > 0


# ─────────────────────────────────────────────────────────────────────────────
# Route validation (gỡ flow không route được bằng chính SUMO)
# ─────────────────────────────────────────────────────────────────────────────

# Các cụm từ trong log SUMO báo một agent không có lộ trình hợp lệ.
_ROUTE_FAIL_KEYS = (
    "could not find route",
    "Disconnected walk",
    "no valid route",
    "invalid route",
    "has no route",
)
# Lấy id ngay sau 'person'/'vehicle', bỏ hậu tố .N của từng lượt sinh (pf_0.3 → pf_0).
_AGENT_ID_RE = re.compile(r"(?:[Pp]erson|[Vv]ehicle)\s+'([A-Za-z0-9_]+?)(?:\.\d+)?'")


def _prune_unroutable(net_path: str, rou_path: str) -> set:
    """Chạy SUMO headless trên một bản 1-lượt của rou_path để phát hiện flow không
    route được, rồi gỡ chúng khỏi rou_path. Trả về tập id flow đã gỡ.

    SUMO là validator đáng tin duy nhất ở đây: duarouter (router intermodal) "dễ tính"
    hơn pedestrian model lúc chạy nên KHÔNG bắt được lỗi "Disconnected walk".
    Nếu không tìm thấy sumo trong PATH thì bỏ qua (không chặn việc sinh map).
    """
    if shutil.which("sumo") is None:
        print("[Cảnh báo] Không thấy 'sumo' trong PATH — bỏ qua bước lọc route hỏng.")
        return set()

    try:
        tree = ET.parse(rou_path)
    except ET.ParseError:
        return set()
    root = tree.getroot()

    # Bản kiểm tra: mỗi flow chỉ sinh 1 lượt (number=1, bỏ period/end) → sim kết thúc sớm
    # khi nhúm agent đầu tiên đi xong/ lỗi, thay vì chạy hết end=3600.
    for tag in ("flow", "personFlow"):
        for el in root.findall(tag):
            el.set("number", "1")
            for attr in ("period", "end"):
                el.attrib.pop(attr, None)
    check_path = rou_path + ".check.tmp.xml"
    tree.write(check_path, encoding="UTF-8", xml_declaration=True)

    bad: set = set()
    try:
        proc = subprocess.run(
            ["sumo", "-n", net_path, "-r", check_path,
             "--no-step-log", "--duration-log.disable", "--ignore-route-errors"],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        for line in (proc.stdout + proc.stderr).splitlines():
            if any(k in line for k in _ROUTE_FAIL_KEYS):
                bad.update(_AGENT_ID_RE.findall(line))
    except Exception as e:
        print(f"[Cảnh báo] Bước lọc route hỏng gặp lỗi ({e}) — giữ nguyên route.")
        bad = set()
    finally:
        try:
            os.remove(check_path)
        except OSError:
            pass

    if not bad:
        return set()

    # Gỡ các flow/personFlow có id nằm trong tập hỏng khỏi rou gốc rồi ghi lại.
    orig = ET.parse(rou_path)
    oroot = orig.getroot()
    for tag in ("flow", "personFlow"):
        for el in list(oroot.findall(tag)):
            if el.get("id") in bad:
                oroot.remove(el)
    if hasattr(ET, "indent"):
        ET.indent(orig, space="    ", level=0)
    orig.write(rou_path, encoding="UTF-8", xml_declaration=True)
    return bad


# ─────────────────────────────────────────────────────────────────────────────
# sumocfg
# ─────────────────────────────────────────────────────────────────────────────

def write_sumocfg(net_path: str, rou_path: str, cfg_path: str) -> None:
    net_name = os.path.basename(net_path)
    rou_name = os.path.basename(rou_path)
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<sumoConfiguration xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
        'xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/sumoConfiguration.xsd">\n'
        '    <input>\n'
        f'        <net-file value="{net_name}"/>\n'
        f'        <route-files value="{rou_name}"/>\n'
        '    </input>\n'
        '</sumoConfiguration>\n'
    )
    out_dir = os.path.dirname(cfg_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(cfg_path, "w", encoding="utf-8") as f:
        f.write(xml)
    print(f"[Thành công] Đã ghi sumocfg → {cfg_path}")


# ─────────────────────────────────────────────────────────────────────────────
# Orchestrator
# ─────────────────────────────────────────────────────────────────────────────

def _sibling_paths(net_path: str) -> Tuple[str, str]:
    """Trả về (rou_path, cfg_path) cùng folder và base name với net_path."""
    base, _ext = os.path.splitext(net_path)
    if base.lower().endswith(".net"):
        base = base[:-4]
    return base + ".rou.xml", base + ".sumocfg"


def build_scenario(osm_file: str,
                   net_path: str,
                   mode: str = "2d",
                   num_junctions: int = 20,
                   edges_per_route: int = 5,
                   algorithm: str = "random",
                   gen_car: bool = True,
                   gen_ped: bool = True,
                   ped_impatience: float = 0.5,
                   car_period: float = 30.0,
                   ped_period: float = 30.0,
                   end_time: float = 3600.0,
                   seed: Optional[int] = None) -> bool:
    ok = convert_osm_to_net_3d_roads(osm_file, net_path, mode=mode)
    if not ok:
        return False

    rou_path, cfg_path = _sibling_paths(net_path)
    ok = generate_routes(
        net_path, rou_path,
        num_junctions=num_junctions,
        edges_per_route=edges_per_route,
        algorithm=algorithm,
        gen_car=gen_car,
        gen_ped=gen_ped,
        ped_impatience=ped_impatience,
        car_period=car_period,
        ped_period=ped_period,
        end_time=end_time,
        seed=seed,
    )
    if not ok:
        print("[Cảnh báo] Không sinh được route nào — net có thể quá nhỏ hoặc thiếu sidewalk.")
        # Vẫn ghi sumocfg để user có thể mở net trong SUMO-GUI; .rou.xml đã được ghi (rỗng)
    write_sumocfg(net_path, rou_path, cfg_path)

    # Trích polygon toà nhà từ .osm → cache cạnh net (toạ độ net SUMO). Chỉ chế độ OSM
    # mới có bước này; runtime gộp vào road_data ("bd") rồi xoá cache. Lỗi ở đây không
    # được làm hỏng việc dựng kịch bản → bọc try/except.
    try:
        from osm.building_extractor import write_buildings_json
        base, _ext = os.path.splitext(net_path)
        if base.lower().endswith(".net"):
            base = base[:-4]
        buildings_path = base + ".buildings.json"
        n_bldg = write_buildings_json(osm_file, net_path, buildings_path)
        print(f"[Thành công] Đã ghi {n_bldg} toà nhà → {buildings_path}")
    except Exception as e:
        print(f"[Cảnh báo] Trích building thất bại ({e}) — bỏ qua khối nhà.")

    return True


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="OSM → .net.xml + .rou.xml + .sumocfg")
    parser.add_argument("osm_file")
    parser.add_argument("-o", "--output", dest="net_path", required=True,
                        help="Đường dẫn .net.xml đầu ra")
    parser.add_argument("-m", "--mode", choices=["2d", "3d"], default="2d")
    parser.add_argument("-n", "--num-junctions", type=int, default=20)
    parser.add_argument("-k", "--edges-per-route", type=int, default=5)
    parser.add_argument("-a", "--algorithm", choices=["random", "max"], default="random")
    parser.add_argument("--no-car", action="store_true")
    parser.add_argument("--no-ped", action="store_true")
    parser.add_argument("--ped-impatience", type=float, default=0.5)
    parser.add_argument("--car-period", type=float, default=30.0,
                        help="Tần suất sinh xe (giây giữa 2 lần khởi hành mỗi flow)")
    parser.add_argument("--ped-period", type=float, default=30.0,
                        help="Tần suất sinh người đi bộ (giây giữa 2 lần khởi hành mỗi flow)")
    parser.add_argument("--end-time", type=float, default=3600.0,
                        help="Độ dài mô phỏng — thời điểm dừng sinh agent (giây)")
    parser.add_argument("--seed", type=int, default=None)
    args = parser.parse_args()

    build_scenario(
        args.osm_file, args.net_path,
        mode=args.mode,
        num_junctions=args.num_junctions,
        edges_per_route=args.edges_per_route,
        algorithm=args.algorithm,
        gen_car=not args.no_car,
        gen_ped=not args.no_ped,
        ped_impatience=args.ped_impatience,
        car_period=args.car_period,
        ped_period=args.ped_period,
        end_time=args.end_time,
        seed=args.seed,
    )
