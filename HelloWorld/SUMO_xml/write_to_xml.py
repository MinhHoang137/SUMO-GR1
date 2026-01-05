import os
import xml.etree.ElementTree as ET
import math

WALL = '@'
FLOOR = '.'


def rotate_2d(v, theta):
    x, y = v
    _theta = math.radians(theta)
    cos_t = math.cos(_theta)
    sin_t = math.sin(_theta)
    x_new = x * cos_t - y * sin_t
    y_new = x * sin_t + y * cos_t
    return (x_new, y_new)

def format_float_to_string(number):
  """
  Chuyển đổi một số thực thành xâu với 2 chữ số sau dấu phẩy.
  
  Args:
    number: Số thực (float) đầu vào.
    
  Returns:
    Một xâu (string) biểu diễn số đó với 2 chữ số thập phân.
  """
  return f"{number:.2f}"



def write_nodes_to_xml(pos_map, output_path, scale=10):
    """
    Ghi danh sách các node vào file .nod.xml theo cú pháp của SUMO.
    
    Args:
        pos_map (dict): Bản đồ vị trí các node với định dạng {key: (x, y, node_id)}.
        output_path (str): Đường dẫn tới file .nod.xml cần ghi.
        scale (float): Hệ số tỉ lệ để chuyển đổi tọa độ 
    """
    # Tạo phần tử gốc <nodes>
    root = ET.Element("nodes")

    # Tạo các phần tử <node>
    for i, (x, y, node_id) in enumerate(pos_map.values()):
        map_x = x * scale
        map_y = y * scale
        node_elem = ET.SubElement(root, "node", {
            "id": node_id,
            "x": f"{map_x:.2f}",
            "y": f"{map_y:.2f}"
        })

    # Tạo cây XML và ghi ra file
    tree = ET.ElementTree(root)
    ET.indent(tree, space="    ", level=0)  # Thêm format đẹp (Python 3.9+)
    tree.write(output_path, encoding="UTF-8", xml_declaration=True)
    print(f"✅ Đã ghi {len(pos_map)} node vào '{output_path}' thành công.")



def write_edges_to_xml(edges, output_path, has_ped_lane=False, numLanes=4, carSpeed=13.9, pedSpeed=1.4):
    """
    Ghi danh sách các cạnh vào file .edg.xml theo cú pháp SUMO.

    Args:
        edges (list[tuple]): Danh sách các cạnh dưới dạng (from_id, to_id).
        output_path (str): Đường dẫn tới file .edg.xml cần ghi.
        has_ped_lane (bool): Có tạo làn đi bộ không.
        numLanes (int): Tổng số làn cho mỗi cạnh (cả 2 chiều).
        carSpeed (float): Tốc độ tối đa cho làn xe (m/s).
        pedSpeed (float): Tốc độ tối đa cho làn đi bộ (m/s).
    """
    root = ET.Element("edges")
    e_cnt = 0

    # ✅ Không vẽ nếu numLanes < 2
    if numLanes < 2:
        print("⚠️ Số làn nhỏ hơn 2 — không xuất cạnh nào.")
        return
    if numLanes < 4:
        numLanes += 2  # thêm 2 làn để dành cho đi bộ
    lanes_per_direction = int(numLanes / 2)

    # ✅ Tạo XML cho từng cạnh (2 chiều)
    for (from_id, to_id) in edges:
        edge_id = f"e{e_cnt}"
        edge_elem = ET.SubElement(root, "edge", {
            "id": edge_id,
            "from": from_id,
            "to": to_id,
            "numLanes": str(lanes_per_direction)
        })

        # Nếu numLanes/2 >= 2 → có làn đi bộ
        # has_ped_lane = (lanes_per_direction >= 2)
        has_ped_lane = True
        lane_index = 0

        if has_ped_lane:
            ET.SubElement(edge_elem, "lane", {
                "index": str(lane_index),
                "allow": "pedestrian",
                "speed": f"{pedSpeed:.1f}",
                "width": "2.0"
            })
            lane_index += 1

        # Thêm làn xe
        for i in range(lane_index, lanes_per_direction):
            ET.SubElement(edge_elem, "lane", {
                "index": str(i),
                "disallow": "pedestrian",
                "speed": f"{carSpeed:.1f}",
                "width": "3.2"
            })

        e_cnt += 1

    # ✅ Ghi file XML ra đĩa
    tree = ET.ElementTree(root)
    ET.indent(tree, space="    ", level=0)
    tree.write(output_path, encoding="UTF-8", xml_declaration=True)
    print(f"✅ Đã ghi {e_cnt} cạnh (2 chiều) vào '{output_path}' thành công.")


def write_crossings_to_con_xml(nod_xml_path, edg_xml_path, output_path, width=2.0):
    """
    Tạo file .con.xml chứa các crossing cho người đi bộ.

    Quy tắc: tại mỗi node, với mỗi cặp cạnh ngược chiều nhau (A->B và B->A)
    sẽ tạo ra 1 crossing. 

    Tham khảo cấu trúc từ TestNetconvert/example.con.xml.

    Args:
        nod_xml_path (str): đường dẫn tới file .nod.xml
        edg_xml_path (str): đường dẫn tới file .edg.xml
        output_path (str): đường dẫn file .con.xml đầu ra
        width (float): bề rộng của crossing
    """
    # Đọc nodes
    tree_nod = ET.parse(nod_xml_path)
    root_nod = tree_nod.getroot()
    nodes = set()
    for node in root_nod.findall("node"):
        nodes.add(node.attrib["id"])

    # Đọc edges và lập tra cứu 2 chiều
    tree_edg = ET.parse(edg_xml_path)
    root_edg = tree_edg.getroot()

    # Map (from_id, to_id) -> edge_id
    dir_edge = {}
    for edge in root_edg.findall("edge"):
        e_id = edge.attrib["id"]
        f = edge.attrib["from"]
        t = edge.attrib["to"]
        dir_edge[(f, t)] = e_id

    # Xác định các cặp ngược chiều theo từng node và chỉ tạo crossing
    # tại node có ít nhất 2 cặp cạnh ngược chiều (2 hàng xóm 2 chiều trở lên)
    con_root = ET.Element("connections")

    # Xây bảng hàng xóm 2 chiều duy nhất cho từng node: neighbor -> (edge_node_to_neighbor, edge_neighbor_to_node)
    neighbors_by_node = {n: {} for n in nodes}
    handled_pairs = set()  # lưu frozenset({a,b}) để không xử lý trùng
    for (a, b), e_ab in dir_edge.items():
        rev = (b, a)
        undirected = frozenset({a, b})
        if rev in dir_edge and undirected not in handled_pairs:
            e_ba = dir_edge[rev]
            handled_pairs.add(undirected)
            if a in neighbors_by_node:
                neighbors_by_node[a][b] = (e_ab, e_ba)
            if b in neighbors_by_node:
                neighbors_by_node[b][a] = (e_ba, e_ab)

    # Tạo crossing nếu node có >= 2 cặp ngược chiều (ít nhất 2 hàng xóm 2 chiều)
    for node_id, nb_dict in neighbors_by_node.items():
        if len(nb_dict) < 2:
            continue
        for nb, (e_forward, e_reverse) in nb_dict.items():
            ET.SubElement(con_root, "crossing", {
                "node": node_id,
                "edges": f"{e_forward} {e_reverse}",
                "width": f"{width:.1f}"
            })

    # Ghi file .con.xml
    tree = ET.ElementTree(con_root)
    ET.indent(tree, space="    ", level=0)
    tree.write(output_path, encoding="UTF-8", xml_declaration=True)
    print(f"✅ Đã ghi {len(con_root.findall('crossing'))} crossing vào '{output_path}'.")

def filter_feasible_pairs(start_list, end_list, edge_file_path):
    """
    Lọc bỏ các cặp điểm bắt đầu/kết thúc không có đường đi (không liên thông).
    Sử dụng BFS trên đồ thị được dựng từ file .edg.xml hoặc .net.xml.
    """
    if not edge_file_path or not os.path.exists(edge_file_path):
        return start_list, end_list

    # 1. Parse Edge File to build Adjacency List
    try:
        tree = ET.parse(edge_file_path)
        root = tree.getroot()
    except Exception as e:
        print(f"⚠️ Lỗi đọc file {edge_file_path}: {e}")
        return start_list, end_list

    adj = {}
    for edge in root.findall(".//edge"):
        eid = edge.get("id", "")
        if eid.startswith(":"): continue # Skip internal edges
        u = edge.get("from")
        v = edge.get("to")
        if u and v:
            if u not in adj: adj[u] = []
            adj[u].append(v)

    # 2. Filter pairs
    new_start = []
    new_end = []
    
    # Cache reachability: start_node -> set of reachable nodes
    reachability_cache = {}
    
    skipped = 0
    
    for s, e in zip(start_list, end_list):
        s_id = s["id"] if isinstance(s, dict) else str(s)
        e_id = e["id"] if isinstance(e, dict) else str(e)
        
        # Nếu điểm bắt đầu không có trong đồ thị, coi như không đi được
        if s_id not in adj:
            skipped += 1
            continue
            
        if s_id not in reachability_cache:
            # BFS để tìm tất cả các node có thể đến được từ s_id
            visited = set()
            queue = [s_id]
            visited.add(s_id)
            while queue:
                curr = queue.pop(0)
                if curr in adj:
                    for neighbor in adj[curr]:
                        if neighbor not in visited:
                            visited.add(neighbor)
                            queue.append(neighbor)
            reachability_cache[s_id] = visited
            
        if e_id in reachability_cache[s_id]:
            new_start.append(s)
            new_end.append(e)
        else:
            skipped += 1
            
    if skipped > 0:
        print(f"ℹ️ Đã lọc bỏ {skipped} tuyến đường không khả thi (không tìm thấy đường đi).")
        
    return new_start, new_end

def write_car_route_to_xml(
    start_list,
    end_list,
    rou_path,
    period=30,
    begin=0.0,
    end_time=3600.0,
    edge_file_path=None,
    use_custom_navigation: bool = False,
    net_file_path: str = "SUMO_xml/HelloWorld.net.xml",
):
    """
    Ghi file .rou.xml chứa các tuyến đường cho xe từ danh sách điểm bắt đầu và kết thúc.

    Mỗi cặp (start, end) sẽ tạo ra một tuyến đường.

    Args:
        start_list (list): Danh sách node bắt đầu.
        end_list (list): Danh sách node kết thúc.
        rou_path (str): Đường dẫn tới file .rou.xml cần ghi.
        period (int): Khoảng thời gian giữa các xe khởi hành (giây) cho mỗi flow.
        edge_file_path (str): Đường dẫn tới file .edg.xml hoặc .net.xml để kiểm tra tính khả thi.
    """
    # Bảo vệ đầu vào
    if not isinstance(start_list, list) or not isinstance(end_list, list):
        raise ValueError("start_list và end_list phải là list")

    # Lọc các tuyến đường khả thi nếu có file edge
    if edge_file_path:
        start_list, end_list = filter_feasible_pairs(start_list, end_list, edge_file_path)

    num_pairs = min(len(start_list), len(end_list))
    if num_pairs == 0:
        # Không có gì để ghi
        # Tạo file rỗng với phần tử <routes> hợp lệ để SUMO không lỗi
        routes_root = ET.Element(
            "routes",
            {
                "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
                "xsi:noNamespaceSchemaLocation": "http://sumo.dlr.de/xsd/routes_file.xsd",
            },
        )
        tree = ET.ElementTree(routes_root)
        ET.indent(tree, space="    ", level=0)
        tree.write(rou_path, encoding="UTF-8", xml_declaration=True)
        return

    # Gốc <routes>
    routes_root = ET.Element(
        "routes",
        {
            "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
            "xsi:noNamespaceSchemaLocation": "http://sumo.dlr.de/xsd/routes_file.xsd",
        },
    )

    # Bạn có thể khai báo vType cho ô tô nếu muốn tuỳ chỉnh; mặc định SUMO dùng passenger
    # ET.SubElement(routes_root, "vType", {"id": "car", "vClass": "passenger"})

    # Nếu dùng Custom Navigation: tạo route edges tường minh (SUMO sẽ không tự tìm đường).
    navigator = None
    if use_custom_navigation:
        try:
            from custom_navigation import CustomNavigator

            navigator = CustomNavigator(net_file_path, enable_parallel=False)
        except Exception as e:
            print(f"⚠️ Không thể khởi tạo CustomNavigator ({e}). Fallback sang fromJunction/toJunction.")
            navigator = None

    for i in range(num_pairs):
        s = start_list[i]
        e = end_list[i]

        s_id = s["id"] if isinstance(s, dict) else str(s)
        e_id = e["id"] if isinstance(e, dict) else str(e)

        if navigator is None:
            ET.SubElement(
                routes_root,
                "flow",
                {
                    "id": f"f_{i}",
                    "begin": f"{begin:.2f}",
                    "end": f"{end_time:.2f}",
                    "period": f"{float(period):.2f}",
                    "fromJunction": s_id,
                    "toJunction": e_id,
                },
            )
            continue

        # Map junction -> edge để chạy A* trên edge graph
        try:
            s_node = navigator.net.getNode(s_id)
            e_node = navigator.net.getNode(e_id)
        except Exception:
            # Nếu junction id không có trong net, fallback
            ET.SubElement(
                routes_root,
                "flow",
                {
                    "id": f"f_{i}",
                    "begin": f"{begin:.2f}",
                    "end": f"{end_time:.2f}",
                    "period": f"{float(period):.2f}",
                    "fromJunction": s_id,
                    "toJunction": e_id,
                },
            )
            continue

        # Chọn 1 outgoing edge từ start junction và 1 incoming edge vào end junction
        start_edges = [ed for ed in s_node.getOutgoing() if not ed.getID().startswith(":")]
        end_edges = [ed for ed in e_node.getIncoming() if not ed.getID().startswith(":")]

        if not start_edges or not end_edges:
            # Không tìm thấy edge hợp lệ, fallback
            ET.SubElement(
                routes_root,
                "flow",
                {
                    "id": f"f_{i}",
                    "begin": f"{begin:.2f}",
                    "end": f"{end_time:.2f}",
                    "period": f"{float(period):.2f}",
                    "fromJunction": s_id,
                    "toJunction": e_id,
                },
            )
            continue

        start_edge_id = start_edges[0].getID()
        end_edge_id = end_edges[0].getID()

        path = navigator.find_path(start_edge_id, end_edge_id)
        if not path:
            # Không tìm được đường, fallback
            ET.SubElement(
                routes_root,
                "flow",
                {
                    "id": f"f_{i}",
                    "begin": f"{begin:.2f}",
                    "end": f"{end_time:.2f}",
                    "period": f"{float(period):.2f}",
                    "fromJunction": s_id,
                    "toJunction": e_id,
                },
            )
            continue

        flow = ET.SubElement(
            routes_root,
            "flow",
            {
                "id": f"f_{i}",
                "begin": f"{begin:.2f}",
                "end": f"{end_time:.2f}",
                "period": f"{float(period):.2f}",
            },
        )
        ET.SubElement(flow, "route", {"edges": " ".join(path)})

    # Ghi file
    tree = ET.ElementTree(routes_root)
    ET.indent(tree, space="    ", level=0)
    # Đảm bảo thư mục tồn tại
    os.makedirs(os.path.dirname(rou_path), exist_ok=True) if os.path.dirname(rou_path) else None
    tree.write(rou_path, encoding="UTF-8", xml_declaration=True)
    print(f"✅ Đã ghi {num_pairs} flow xe vào '{rou_path}' thành công.")

    if navigator is not None:
        try:
            navigator.close()
        except Exception:
            pass


def write_ped_route_to_xml(start_list, end_list, rou_path, period=30, impatience=1.0, vtype_id=None, begin=0.0, end_time=3600.0, edge_file_path=None):
    """
    Ghi thêm các tuyến đường cho người đi bộ vào file .rou.xml đã tồn tại (không ghi đè nội dung xe ô tô).

    Cấu trúc tham khảo như TestNetconvert/example.rou.xml: sử dụng <personFlow> và <personTrip>
    với fromJunction/toJunction. Hàm này sẽ:
      - Tạo (nếu chưa có) vType cho người đi bộ với id = ped_{impatience}
      - Thêm các personFlow, mỗi flow có một personTrip đi từ start_id đến end_id

    Args:
        start_list (list): Danh sách node bắt đầu (mỗi phần tử có 'id' là id junction, hoặc string id).
        end_list (list): Danh sách node kết thúc.
        rou_path (str): Đường dẫn file .rou.xml (đã được tạo trước bởi write_car_route_to_xml).
        period (int|float): Chu kỳ sinh người đi bộ (giây) cho mỗi flow.
        impatience (float): Mức impatience cho vType người đi bộ (được dùng trong id và thuộc tính). Giá trị sẽ được ép trong [0, 1].
        vtype_id (str|None): Nếu None, tự sinh theo định dạng ped_{impatience}.
        begin (float): Thời điểm bắt đầu.
        end_time (float): Thời điểm kết thúc.
        edge_file_path (str): Đường dẫn tới file .edg.xml hoặc .net.xml để kiểm tra tính khả thi.
    """
    # Đọc (hoặc tạo mới) cây XML hiện có
    routes_root = None
    if os.path.isfile(rou_path):
        try:
            tree = ET.parse(rou_path)
            routes_root = tree.getroot()
        except Exception:
            routes_root = None

    if routes_root is None:
        # Tạo mới root <routes>
        routes_root = ET.Element(
            "routes",
            {
                "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
                "xsi:noNamespaceSchemaLocation": "http://sumo.dlr.de/xsd/routes_file.xsd",
            },
        )
        tree = ET.ElementTree(routes_root)
    else:
        tree = ET.ElementTree(routes_root)

    # Bảo vệ đầu vào
    if not isinstance(start_list, list) or not isinstance(end_list, list):
        raise ValueError("start_list và end_list phải là list")

    # Lọc các tuyến đường khả thi nếu có file edge
    if edge_file_path:
        start_list, end_list = filter_feasible_pairs(start_list, end_list, edge_file_path)

    num_pairs = min(len(start_list), len(end_list))
    if num_pairs == 0:
        # Không có gì để thêm, nhưng vẫn ghi lại file hiện trạng
        ET.indent(tree, space="    ", level=0)
        tree.write(rou_path, encoding="UTF-8", xml_declaration=True)
        return

    # Ép impatience về [0, 1]
    try:
        _imp = float(impatience)
    except Exception:
        _imp = 1.0
    clamped_imp = max(0.0, min(1.0, _imp))

    # Tạo id vType nếu cần (đảm bảo an toàn ký tự)
    def fmt_imp(val: float) -> str:
        # Dùng tối đa 2 chữ số thập phân và thay '.' thành '_'
        return f"{val:.2f}".rstrip('0').rstrip('.').replace('.', '_')

    if vtype_id is None:
        vtype_id = f"ped_{fmt_imp(clamped_imp)}"

    # Kiểm tra vType tồn tại chưa
    existing_vtypes = {vt.attrib.get('id') for vt in routes_root.findall('vType')}
    if vtype_id not in existing_vtypes:
        ET.SubElement(
            routes_root,
            "vType",
            {"id": vtype_id, "vClass": "pedestrian", "impatience": f"{clamped_imp:.2f}"},
        )
    else:
        # Cập nhật impatience cho vType hiện có để đảm bảo nằm trong [0,1]
        for vt in routes_root.findall('vType'):
            if vt.attrib.get('id') == vtype_id:
                vt.set('impatience', f"{clamped_imp:.2f}")
                break

    # Tạo id duy nhất cho personFlow dựa trên số lượng sẵn có
    existing_pf = [pf.attrib.get('id') for pf in routes_root.findall('personFlow')]
    used_ids = set(filter(None, existing_pf))

    def next_pf_id(prefix: str, start_index: int = 0) -> str:
        i = start_index
        while True:
            cand = f"{prefix}{i}"
            if cand not in used_ids:
                used_ids.add(cand)
                return cand
            i += 1

    # Ghi các personFlow
    for i in range(num_pairs):
        s = start_list[i]
        e = end_list[i]
        s_id = s["id"] if isinstance(s, dict) else str(s)
        e_id = e["id"] if isinstance(e, dict) else str(e)

        pf_id = next_pf_id("pf_")
        pf = ET.SubElement(
            routes_root,
            "personFlow",
            {
                "id": pf_id,
                "type": vtype_id,
                "begin": f"{float(begin):.2f}",
                "end": f"{float(end_time):.2f}",
                "period": f"{float(period):.2f}",
            },
        )
        ET.SubElement(pf, "personTrip", {"fromJunction": s_id, "toJunction": e_id})

    # Ghi lại file
    ET.indent(tree, space="    ", level=0)
    # Đảm bảo thư mục tồn tại
    os.makedirs(os.path.dirname(rou_path), exist_ok=True) if os.path.dirname(rou_path) else None
    tree.write(rou_path, encoding="UTF-8", xml_declaration=True)
    print(f"✅ Đã ghi {num_pairs} personFlow (người đi bộ) vào '{rou_path}' thành công.")

