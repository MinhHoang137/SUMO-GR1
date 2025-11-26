import os
import xml.etree.ElementTree as ET
import math
import sys
from SUMO_xml import write_to_xml, map_header

# Add the parent directory to the sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


WALL = '@'
FLOOR = '.'

    
def get_biggest_angle(dir_list):
    """
    Tìm góc lớn nhất giữa các hướng trong danh sách dir_list.
    
    Args:
        dir_list (list): Danh sách các hướng dưới dạng [dx, dy].
        
    Returns:
        Góc lớn nhất (tính bằng độ) giữa các hướng.
    """
    max_angle = 0
    num_dirs = len(dir_list)
    
    for i in range(num_dirs):
        for j in range(i + 1, num_dirs):
            dx1, dy1 = dir_list[i]
            dx2, dy2 = dir_list[j]
            
            # Tính tích vô hướng
            dot_product = dx1 * dx2 + dy1 * dy2
            mag1 = math.sqrt(dx1**2 + dy1**2)
            mag2 = math.sqrt(dx2**2 + dy2**2)
            
            if mag1 == 0 or mag2 == 0:
                continue
            
            cos_angle = dot_product / (mag1 * mag2)
            # Giới hạn giá trị cos_angle trong khoảng [-1, 1] để tránh lỗi do làm tròn số
            cos_angle = max(-1, min(1, cos_angle))
            angle = math.acos(cos_angle) * (180 / math.pi) # Chuyển sang độ
            
            if angle > max_angle:
                max_angle = angle
                
    return max_angle


def get_point_degree(grid, x, y, mW, mH):
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
    directions = [[1, 0], [1, 1], [0, 1], [-1, 1], [-1, 0], [-1, -1], [0, -1], [1, -1]] # 8 hướng xung quanh
    
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
    
    if degree == 3:
        angle = get_biggest_angle(inc_dir_list)
        if angle > 90:
            degree = 0
    
    if degree == 4:
        angle = get_biggest_angle(inc_dir_list)
        if angle > 135:
            degree = 0
    
    if degree > 4 or degree <= 1:
        degree = 0
    
    if degree == 0:
        inc_dir_list = []

    return degree, inc_dir_list

def get_valid_points(grid, mW, mH):
    """
    Lấy tất cả các điểm tường hợp lệ từ lưới (grid).
    
    Args:
        grid: Mảng 2 chiều biểu diễn bản đồ.
        mW: Chiều rộng của lưới.
        mH: Chiều cao của lưới.
        
    Returns:
        Danh sách các điểm tường hợp lệ dưới dạng [x, y].
    """
    points = []
    
    for y in range(mH):
        for x in range(mW):
            degree, _ = get_point_degree(grid, x, y, mW, mH)
            if degree > 0:
                can_add = True
                # check distance with existing points
                for point in points:
                    attitude = math.sqrt((point[0] - x) ** 2 + (point[1] - y) ** 2)
                    if attitude < 1.4:
                        can_add = False
                        break
                    
                if can_add:
                    points.append([x, y])
    return points

def can_2_points_connect(grid, p1, p2):
    """
    Kiểm tra xem hai điểm có thể kết nối trực tiếp không (không có chướng ngại vật ở giữa).
    
    Args:
        grid: Mảng 2 chiều biểu diễn bản đồ.
        p1: Điểm đầu tiên dưới dạng [x, y].
        p2: Điểm thứ hai dưới dạng [x, y].
        
    Returns:
        True nếu hai điểm có thể kết nối trực tiếp, False nếu không thể.
    """
    x1, y1 = p1
    x2, y2 = p2
    
    dx = x2 - x1
    dy = y2 - y1
    steps = max(abs(dx), abs(dy))
    
    if steps == 0:
        return True  # Cùng một điểm
    
    x_inc = dx / steps
    y_inc = dy / steps
    
    x, y = x1, y1
    for _ in range(int(steps)):
        x += x_inc
        y += y_inc
        grid_x, grid_y = round(x), round(y)
        if grid[grid_y][grid_x] != WALL:
            return False  # Gặp chướng ngại vật
    
    return True

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

def get_node_position_list(grid, mW, mH):
    """
    Lấy danh sách vị trí các node từ lưới (grid).
    """
    n_cnt = 0
    node_position_list = {}

    points = get_valid_points(grid, mW, mH)

    for point1 in points:
        neighbors = [point1]
        for point2 in points:
            if point1 == point2:
                continue
            if can_2_points_connect(grid, point1, point2):
                neighbors.append(point2)
            if len(neighbors) > 3:
                break
        pos_x = 0
        pos_y = 0
        for neighbor in neighbors:
            pos_x += neighbor[0]
            pos_y += neighbor[1]
        pos_x /= len(neighbors)
        pos_y /= len(neighbors)
        if not check_node_valid(grid, node_position_list, pos_x, pos_y, mW, mH):
            continue
        node_position_list[f"{pos_x:.2f}_{pos_y:.2f}"] = (pos_x, pos_y, f"n_{n_cnt}")
        n_cnt += 1

    return node_position_list

def write_city_edges_to_xml(grid, pos_map, output_path, numLanes=4, carSpeed=13.9, pedSpeed=1.4):
    """
    Ghi các cạnh (edges) vào tệp XML dựa trên lưới (grid) và bản đồ vị trí node (pos_map).
    
    Args:
        grid: Mảng 2 chiều biểu diễn bản đồ.
        pos_map: Bản đồ vị trí các node dưới dạng dict{"x_y": (x, y, id)}.
        mH: Chiều cao của lưới.
        mW: Chiều rộng của lưới.
        output_path: Đường dẫn tệp XML đầu ra.
        numLanes: Số làn đường cho mỗi cạnh.
        carSpeed: Tốc độ xe hơi (m/s).
        pedSpeed: Tốc độ người đi bộ (m/s).
    """
    edges = []
    for sx, sy, sid in pos_map.values():
        for tx, ty, tid in pos_map.values():
            if sid == tid:
                continue
            if can_2_points_connect(grid, (sx, sy), (tx, ty)):
                edges.append((sid, tid))
    write_to_xml.write_edges_to_xml(edges, output_path, has_ped_lane=True, numLanes=numLanes, carSpeed=carSpeed, pedSpeed=pedSpeed)
    
def visualize_nodes(grid, pos_map):
    """
    Hiển thị các node và kết nối giữa chúng dưới dạng đồ thị.
    """
    try:
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError:
        print("Vui lòng cài đặt matplotlib và numpy để sử dụng chức năng này: pip install matplotlib numpy")
        return

    fig, ax = plt.subplots(figsize=(10, 10))
    
    # Hiển thị grid nền
    grid_display = np.array([[0 if cell == FLOOR else 1 for cell in row] for row in grid])
    ax.imshow(grid_display, cmap='Greys', origin='lower')

    nodes = list(pos_map.values())
    positions = {node[2]: (node[0], node[1]) for node in nodes}

    # Vẽ các node
    x_coords = [pos[0] for pos in positions.values()]
    y_coords = [pos[1] for pos in positions.values()]
    ax.scatter(x_coords, y_coords, c='r', s=50, zorder=5)

    # Ghi nhãn cho các node
    for node_id, (x, y) in positions.items():
        ax.text(x + 0.5, y + 0.5, node_id, fontsize=9, ha='center', color='blue')

    # Vẽ các cạnh kết nối
    for sx, sy, sid in nodes:
        for tx, ty, tid in nodes:
            if sid == tid:
                continue
            if can_2_points_connect(grid, (sx, sy), (tx, ty)):
                ax.plot([sx, tx], [sy, ty], 'b-', lw=1)

    ax.set_title("Sơ đồ các Node và kết nối")
    ax.set_xlabel("Tọa độ X")
    ax.set_ylabel("Tọa độ Y")
    plt.grid(True)
    plt.show()

def create_map(city_path, numLanes=4, carSpeed=13.9, pedSpeed=1.4):
    """
    Tạo bản đồ thành phố từ tệp đầu vào và ghi các cạnh vào tệp XML.
    
    Args:
        city_path: Đường dẫn tệp bản đồ thành phố.
        numLanes: Số làn đường cho mỗi cạnh.
        carSpeed: Tốc độ xe hơi (m/s).
        pedSpeed: Tốc độ người đi bộ (m/s).
    """
    grid, mW, mH = map_header.parse_map_file(city_path)
    if grid is None:
        print("Không thể tạo bản đồ do lỗi đọc tệp.")
        return
    
    pos_map = get_node_position_list(grid, mW, mH)
    visualize_nodes(grid, pos_map) # Hiển thị đồ thị
    _nod_xml_path = "SUMO_xml/HelloWorld.nod.xml"
    _edg_xml_path = "SUMO_xml/HelloWorld.edg.xml"
    _net_xml_path = "SUMO_xml/HelloWorld.net.xml"
    _con_xml_path = "SUMO_xml/HelloWorld.con.xml"

     # Ghi file .nod.xml và .edg.xml
    write_to_xml.write_nodes_to_xml(pos_map, _nod_xml_path)
    write_city_edges_to_xml(grid, pos_map, _edg_xml_path, numLanes=numLanes, carSpeed=carSpeed, pedSpeed=pedSpeed)
    # Tạo crossings (.con.xml) từ .nod.xml và .edg.xml (dùng width mặc định trong hàm)
    write_to_xml.write_crossings_to_con_xml(_nod_xml_path, _edg_xml_path, _con_xml_path)
    os.system(f"netconvert -n {_nod_xml_path} -e {_edg_xml_path} -x {_con_xml_path} -o {_net_xml_path} --offset.x 0 --offset.y 0")
    print(f"\n✅ Bản đồ SUMO đã được tạo thành công tại: {_net_xml_path}\n")

if __name__ == "__main__":
    # Ví dụ sử dụng
    city_map_path = "../Boston_0_256.map"  # Đường dẫn tệp bản đồ thành phố
    create_map(city_map_path, numLanes=4, carSpeed=13.9, pedSpeed=1.4)