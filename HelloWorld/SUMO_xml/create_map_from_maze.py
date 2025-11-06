# Chú ý: đây là thuật toán tìm nút tối ưu từ mê cung để tạo bản đồ SUMO,
# tạm thời không phù hợp với bài toán hiện tại
import os
import xml.etree.ElementTree as ET
import math
from SUMO_xml import write_to_xml

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



def parse_map_file(filepath):
    """
    Đọc và phân tích tệp .map.
    
    Hàm này mở tệp tại 'filepath', đọc header để lấy
    chiều rộng (width) và chiều cao (height), sau đó
    đọc ma trận bản đồ vào một mảng 2 chiều.
    
    Trả về:
        Một tuple (grid, width, height) nếu thành công.
        Một tuple (None, 0, 0) nếu có lỗi.
    """
    try:
        with open(filepath, 'r') as f:
            lines = f.readlines()
            
        header = {}
        map_data_start_index = -1
        
        # --- Phần 2: Đọc header để lấy width và height ---
        for i, line in enumerate(lines):
            line = line.strip() # Xóa khoảng trắng thừa hoặc ký tự xuống dòng
            
            if line.startswith('height'):
                header['height'] = int(line.split(' ')[1])
            elif line.startswith('width'):
                header['width'] = int(line.split(' ')[1])
            elif line.startswith('map'):
                # Đánh dấu vị trí bắt đầu của ma trận
                map_data_start_index = i + 1
                break
        
        # Kiểm tra xem đã tìm thấy đủ thông tin header chưa
        if map_data_start_index == -1 or 'width' not in header or 'height' not in header:
            print(f"Lỗi: Tệp '{filepath}' có định dạng không hợp lệ hoặc thiếu header.")
            return None, 0, 0
            
        width = header['width']
        height = header['height']
    

        # --- Phần 3: Đọc ma trận và lưu vào mảng 2 chiều ---
        grid = []
        map_lines = lines[map_data_start_index:] # Chỉ lấy các dòng từ 'map' trở đi
        
        for y in range(height):
            if y >= len(map_lines):
                # Trường hợp tệp bị thiếu dòng so với header
                print(f"Lỗi: Dữ liệu bản đồ bị thiếu. Mong đợi {height} hàng, chỉ tìm thấy {y}.")
                return None, 0, 0
            
            # Lấy đúng 'width' ký tự và chuyển thành một danh sách (list)
            row_data = list(map_lines[y].strip()[:width])
            
            if len(row_data) != width:
                print(f"Lỗi: Hàng {y} có chiều rộng không chính xác. Mong đợi {width}, tìm thấy {len(row_data)}.")
                return None, 0, 0
                
            # Thêm hàng (danh sách ký tự) vào ma trận 'grid'
            grid.append(row_data)
            
        return grid, width, height

    except FileNotFoundError:
        print(f"Lỗi: Không tìm thấy tệp tại đường dẫn '{filepath}'")
        return None, 0, 0
    except Exception as e:
        print(f"Đã xảy ra lỗi khi đọc tệp: {e}")
        return None, 0, 0
    
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
    for node_pos in iterable:
        attitude = math.sqrt((node_pos[0] - pos_x) ** 2 + (node_pos[1] - pos_y) ** 2)
        if attitude < 0.1:
            return False

    return True


def get_node_position_list(grid, mW, mH, numLanes=4):
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



# cách dùng hàm: create_map_from_maze_file("duongdan/to/mapfile.map", 2)
# số làn (numLanes) là tổng số làn (cả 2 chiều), là số cuối cùng trong tên tệp .map
# cần nhập chính xác, nếu không sẽ không tạo được bản đồ đúng
def create_map_from_maze_file(filepath, numLanes):
    """
    Tạo bản đồ từ tệp lưới (maze file) theo định dạng SUMO.

    Args:
        filepath (str): Đường dẫn tới tệp lưới.
        numLanes (int): Số làn đường.

    Returns:
        None
    """
    print(f"Đang xử lý tệp: {filepath}\n")
    
    # Gọi hàm để phân tích tệp
    grid, width, height = parse_map_file(filepath)

    # Nếu hàm trả về lỗi (grid là None), thì dừng lại
    if grid is None:
        print("Không thể xử lý tệp.")
        return
    print(f"Chiều rộng: {width}, Chiều cao: {height}\n")

    pos_map = get_node_position_list(grid, width, height, numLanes)

    _nod_xml_path = "SUMO_xml/HelloWorld.nod.xml"
    _edg_xml_path = "SUMO_xml/HelloWorld.edg.xml"
    _net_xml_path = "SUMO_xml/HelloWorld.net.xml"
    _con_xml_path = "SUMO_xml/HelloWorld.con.xml"

     # Ghi file .nod.xml và .edg.xml
    write_to_xml.write_nodes_to_xml(pos_map, _nod_xml_path)
    write_to_xml.write_edges_to_xml(grid, pos_map, height, width, _edg_xml_path, numLanes=numLanes)
    # Tạo crossings (.con.xml) từ .nod.xml và .edg.xml (dùng width mặc định trong hàm)
    write_to_xml.write_crossings_to_con_xml(_nod_xml_path, _edg_xml_path, _con_xml_path)
    os.system(f"netconvert -n {_nod_xml_path} -e {_edg_xml_path} -x {_con_xml_path} -o {_net_xml_path} --offset.x 0 --offset.y 0")
    print(f"\n✅ Bản đồ SUMO đã được tạo thành công tại: {_net_xml_path}\n")
