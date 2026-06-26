
import os
import warnings
import xml.etree.ElementTree as ET
import math
from SUMO_xml import write_to_xml, map_header

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


    
def get_node_degree(grid, x, y, mW, mH):
    if grid[y][x] != WALL:
        return 0 , []
    """
    Lấy bậc (degree) của một điểm tường trong lưới (grid).
    
    Args:
        grid: Mảng 2 chiều biểu diễn bản đồ.
        x: Tọa độ x của điểm.
        y: Tọa độ y của điểm.
        mW: Chiều rộng của lưới.
        mH: Chiều cao của lưới.
        
    Returns:
        Bậc (degree) của điểm tại (x, y).
        Danh sách các hướng (incDir) mà điểm này kết nối với các điểm kề.
    """
    degree = 0
    directions = [[1, 0], [0, 1], [-1, 0], [0, -1]]  # Phải, Dưới, Trái, Trên
    
    inc_dir_list = []

    for dx, dy in directions:
        nx, ny = x + dx, y + dy
        if 0 <= nx < mW and 0 <= ny < mH:
            if grid[ny][nx] == WALL:
                degree += 1
                inc_dir_list.append([dx, dy])
    if degree == 2:
        # Kiểm tra xem hai hướng có thẳng hàng không, dùng tích vô hướng
        dot_product = inc_dir_list[0][0] * inc_dir_list[1][0] + inc_dir_list[0][1] * inc_dir_list[1][1]
        if dot_product != 0: # đây là 1 bức tường thẳng
            degree = 0

    return degree, inc_dir_list

def check_node_valid(grid, node_position_map, pos_x, pos_y, mW, mH):
    if pos_x <= 0 or pos_x >= mW or pos_y <= 0 or pos_y >= mH:
        return False
    # Lấy chỉ số ô trong grid
    x_int = int(pos_x)
    y_int = int(pos_y)
    if grid[y_int][x_int] == WALL:
        return False
    
    # Hỗ trợ cả danh sách [(x,y)] và dict{"x_y": (x,y)}
    iterable = node_position_map.values() if isinstance(node_position_map, dict) else node_position_map
    
    # Kiểm tra khoảng cách với các node đã có
    for node_pos in iterable:
        attitude = math.sqrt((node_pos[0] - pos_x) ** 2 + (node_pos[1] - pos_y) ** 2)
        if attitude < 0.1:
            return False

    return True


def get_node_position_list(grid, mW, mH, numLanes=4):
    """
    Lấy danh sách vị trí các node từ lưới (grid).
    """
    n_cnt = 0
    node_position_list = {}
    offset = 0
    if numLanes <= 0:
        return node_position_list
    elif numLanes == 1:
        offset = 1
    else:
        if numLanes % 2 == 0:
            offset = (numLanes+1) / 2
        else:
            offset = numLanes / 2
    for y in range(mH):
        for x in range(mW):
            if grid[y][x] == WALL:
                degree, inc_dir_list = get_node_degree(grid, x, y, mW, mH)
                if degree == 1:
                    spawn_vec_1_x = rotate_2d(inc_dir_list[0], 135)[0] * math.sqrt(2)
                    spawn_vec_1_y = rotate_2d(inc_dir_list[0], 135)[1] * math.sqrt(2)
                    spawn_vec_2_x = rotate_2d(inc_dir_list[0], -135)[0] * math.sqrt(2)
                    spawn_vec_2_y = rotate_2d(inc_dir_list[0], -135)[1] * math.sqrt(2)
                    pos_x = x + spawn_vec_1_x * offset
                    pos_y = y + spawn_vec_1_y * offset
                    if check_node_valid(grid, node_position_list, pos_x, pos_y, mW, mH):
                        node_position_list[f"{format_float_to_string(pos_x)}_{format_float_to_string(pos_y)}"] = (pos_x, pos_y, f"n_{n_cnt}")
                        n_cnt += 1
                    pos_x = x + spawn_vec_2_x * offset
                    pos_y = y + spawn_vec_2_y * offset
                    if check_node_valid(grid, node_position_list, pos_x, pos_y, mW, mH):
                        node_position_list[f"{format_float_to_string(pos_x)}_{format_float_to_string(pos_y)}"] = (pos_x, pos_y, f"n_{n_cnt}")
                        n_cnt += 1
                elif degree >= 3:
                    for i in range(degree):
                        spawn_vec_x = inc_dir_list[i][0] + inc_dir_list[(i + 1) % degree][0]
                        spawn_vec_y = inc_dir_list[i][1] + inc_dir_list[(i + 1) % degree][1]
                        pos_x = x + spawn_vec_x * offset
                        pos_y = y + spawn_vec_y * offset
                        if check_node_valid(grid, node_position_list, pos_x, pos_y, mW, mH):
                            node_position_list[f"{format_float_to_string(pos_x)}_{format_float_to_string(pos_y)}"] = (pos_x, pos_y, f"n_{n_cnt}")
                            n_cnt += 1
                elif degree == 2:
                    spawn_vec_x = inc_dir_list[0][0] + inc_dir_list[1][0]
                    spawn_vec_y = inc_dir_list[0][1] + inc_dir_list[1][1]
                    pos_x = x + spawn_vec_x * offset
                    pos_y = y + spawn_vec_y * offset
                    if check_node_valid(grid, node_position_list, pos_x, pos_y, mW, mH):
                        node_position_list[f"{format_float_to_string(pos_x)}_{format_float_to_string(pos_y)}"] = (pos_x, pos_y, f"n_{n_cnt}")
                        n_cnt += 1
                    pos_x = x - spawn_vec_x * offset
                    pos_y = y - spawn_vec_y * offset
                    if check_node_valid(grid, node_position_list, pos_x, pos_y, mW, mH):
                        node_position_list[f"{format_float_to_string(pos_x)}_{format_float_to_string(pos_y)}"] = (pos_x, pos_y, f"n_{n_cnt}")
                        n_cnt += 1

    return node_position_list

def write_maze_edges_to_xml(grid, pos_map, mH, mW, output_path, numLanes=4, carSpeed=13.9, pedSpeed=1.4, car_lanes_per_dir=None):
    """
    Ghi danh sách các cạnh của mê cung vào file .edg.xml theo cú pháp SUMO.

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
        numLanes (int): Tổng số làn cho mỗi cạnh (cả 2 chiều). Bị ghi đè nếu car_lanes_per_dir được cung cấp.
        carSpeed (float): Tốc độ tối đa cho làn xe (m/s).
        pedSpeed (float): Tốc độ tối đa cho làn đi bộ (m/s).
        car_lanes_per_dir (int|None): Số làn XE mỗi chiều (mỗi bên), luôn kèm 1 làn đi bộ. Nếu khác None sẽ ghi đè 'numLanes'.
    """
    edges = []


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

    write_to_xml.write_edges_to_xml(edges, output_path, True, numLanes=numLanes, carSpeed=carSpeed, pedSpeed=pedSpeed, car_lanes_per_dir=car_lanes_per_dir)


def visualize_network(nod_file_path, edg_file_path, show_id=True, figsize=(10, 10)):
    # Import matplotlib lazily so the rest of the pipeline doesn't require it
    try:
        import matplotlib.pyplot as plt # type: ignore
    except ImportError:
        print("matplotlib is not installed. Skipping visualization. If you need plots, install matplotlib.")
        return
    """
    Vẽ đồ thị mạng lưới node–edge từ file .nod.xml và .edg.xml (theo cú pháp SUMO).

    Args:
        nod_file_path (str): Đường dẫn tới file node (.nod.xml)
        edg_file_path (str): Đường dẫn tới file edge (.edg.xml)
        show_id (bool): Có hiển thị id của node không
        figsize (tuple): Kích thước hình vẽ matplotlib
    """
    # --- Đọc node ---
    tree_nod = ET.parse(nod_file_path)
    root_nod = tree_nod.getroot()
    nodes = {}

    for node in root_nod.findall("node"):
        node_id = node.attrib["id"]
        x = float(node.attrib["x"])
        y = float(node.attrib["y"])
        nodes[node_id] = (x, y)

    # --- Đọc edge ---
    tree_edg = ET.parse(edg_file_path)
    root_edg = tree_edg.getroot()
    edges = []

    for edge in root_edg.findall("edge"):
        from_node = edge.attrib["from"]
        to_node = edge.attrib["to"]
        edges.append((from_node, to_node))

    # --- Vẽ ---
    plt.figure(figsize=figsize)
    
    # Vẽ cạnh
    for (from_id, to_id) in edges:
        if from_id in nodes and to_id in nodes:
            x1, y1 = nodes[from_id]
            x2, y2 = nodes[to_id]
            plt.plot([x1, x2], [y1, y2], color="gray", linewidth=1.5, alpha=0.6, zorder=1)
        else:
            print(f"⚠️ Cảnh báo: Edge {from_id} → {to_id} chứa node không tồn tại!")

    # Vẽ node
    xs, ys = zip(*nodes.values())
    plt.scatter(xs, ys, color="deepskyblue", edgecolors="black", s=80, zorder=3)

    if show_id:
        for node_id, (x, y) in nodes.items():
            plt.text(x + 2, y + 2, node_id, fontsize=8, color="navy")

    plt.title("SUMO Network Visualization")
    plt.xlabel("X coordinate (m)")
    plt.ylabel("Y coordinate (m)")
    plt.grid(True, linestyle="--", alpha=0.4)
    plt.gca().set_aspect("equal", adjustable="box")
    plt.show()



def create_map_from_maze_file(filepath, numLanes, practiceNumLanes=8):
    """Tạo bản đồ từ tệp lưới (maze file) theo định dạng SUMO. Không còn được launcher gọi trực tiếp.

    Args:
        filepath (str): Đường dẫn tới tệp lưới.
        numLanes (int): Số làn đường dùng để phân tích tệp .map.
        practiceNumLanes (int): Số làn đường cho mục đích dựng bản đồ thực tế (mặc định là 8).

    Returns:
        None
    """
    warnings.warn(
        "create_map_from_maze_file() không còn được dùng; dùng "
        "naive_map_creator.naive_create_map() thay thế.",
        DeprecationWarning,
        stacklevel=2,
    )
    print(f"Đang xử lý tệp: {filepath}\n")
    
    # Gọi hàm để phân tích tệp
    grid, width, height = map_header.parse_map_file(filepath)

    # Nếu hàm trả về lỗi (grid là None), thì dừng lại
    if grid is None:
        print("Không thể xử lý tệp.")
        return False
    print(f"Chiều rộng: {width}, Chiều cao: {height}\n")

    pos_map = get_node_position_list(grid, width, height, numLanes)

    _nod_xml_path = "SUMO_xml/HelloWorld.nod.xml"
    _edg_xml_path = "SUMO_xml/HelloWorld.edg.xml"
    _net_xml_path = "SUMO_xml/HelloWorld.net.xml"
    _con_xml_path = "SUMO_xml/HelloWorld.con.xml"

     # Ghi file .nod.xml và .edg.xml
    write_to_xml.write_nodes_to_xml(pos_map, _nod_xml_path, scale = 20)
    write_maze_edges_to_xml(grid, pos_map, height, width, _edg_xml_path, numLanes=practiceNumLanes)
    # Tạo crossings (.con.xml) từ .nod.xml và .edg.xml (dùng width mặc định trong hàm)
    write_to_xml.write_crossings_to_con_xml(_nod_xml_path, _edg_xml_path, _con_xml_path)
    os.system(f"netconvert -n {_nod_xml_path} -e {_edg_xml_path} -x {_con_xml_path} -o {_net_xml_path} --offset.x 0 --offset.y 0 --no-turnarounds.geometry false --no-turnarounds false")
    print(f"\n✅ Bản đồ SUMO đã được tạo thành công tại: {_net_xml_path}\n")
    return True
