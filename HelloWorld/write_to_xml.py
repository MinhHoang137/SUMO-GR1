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


def write_edges_to_xml(grid, pos_map, mH, mW, output_path, numLanes=4, carSpeed=13.9, pedSpeed=1.4):
    """
    Ghi danh sách các cạnh vào file .edg.xml theo cú pháp SUMO.

    Quy tắc:
    - numLanes là tổng số làn (cả 2 chiều)
    - Mỗi hướng chỉ chiếm numLanes / 2 làn
    - Nếu (numLanes/2) >= 2 thì thêm 1 làn đi bộ (index=0)
    - Các làn còn lại dành cho xe
    - ID cạnh dùng định dạng: e0, e1, e2, ...
    Args:
        grid (list[list[str]]): Lưới mê cung 2D.
        pos_map (dict): Bản đồ vị trí các node với định dạng {key: (x, y, node_id)}.
        mH (int): Chiều cao lưới.
        mW (int): Chiều rộng lưới.
        output_path (str): Đường dẫn tới file .edg.xml cần ghi.
        numLanes (int): Tổng số làn cho mỗi cạnh (cả 2 chiều).
        carSpeed (float): Tốc độ tối đa cho làn xe (m/s).
        pedSpeed (float): Tốc độ tối đa cho làn đi bộ (m/s).
    """
    import xml.etree.ElementTree as ET

    root = ET.Element("edges")
    edges = []
    e_cnt = 0

    # ✅ Sinh danh sách cạnh 1 chiều (dựa trên node thực)
    for start_key, (sx, sy, s_id) in pos_map.items():
        int_x = int(sx)
        int_y = int(sy)
        directions = [(1, 0), (0, 1), (-1, 0), (0, -1)]  # phải, xuống, trái, lên

        for dx, dy in directions:
            for i in range(1, max(mW, mH)):
                nx, ny = int_x + dx * i, int_y + dy * i
                if nx < 0 or nx >= mW or ny < 0 or ny >= mH:
                    break
                if grid[ny][nx] == WALL:
                    break

                end_x, end_y = sx + dx * i, sy + dy * i
                end_key = f"{format_float_to_string(end_x)}_{format_float_to_string(end_y)}"

                if end_key in pos_map:
                    _, _, t_id = pos_map[end_key]
                    edges.append((s_id, t_id))
                    break

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