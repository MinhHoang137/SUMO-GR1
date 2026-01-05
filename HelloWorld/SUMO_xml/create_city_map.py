import os
import xml.etree.ElementTree as ET
import math
import sys

# Add the parent directory to the sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from SUMO_xml import write_to_xml, map_header


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
            if degree == 3:
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

def can_2_points_connect(grid, p1, p2, target_type=WALL, ignore_endpoints=False):
    """
    Kiểm tra xem hai điểm có thể kết nối trực tiếp không (không có chướng ngại vật ở giữa).
    Sử dụng thuật toán Bresenham để cải thiện độ chính xác.
    
    Args:
        grid: Mảng 2 chiều biểu diễn bản đồ.
        p1: Điểm đầu tiên dưới dạng [x, y].
        p2: Điểm thứ hai dưới dạng [x, y].
        target_type: Loại ô cho phép đi qua (WALL hoặc FLOOR). Mặc định là WALL.
        ignore_endpoints: Nếu True, bỏ qua kiểm tra loại ô tại điểm đầu và điểm cuối.
        
    Returns:
        True nếu hai điểm có thể kết nối trực tiếp, False nếu không thể.
    """
    x1, y1 = p1 # Lấy tọa độ x, y của điểm đầu
    x2, y2 = p2 # Lấy tọa độ x, y của điểm cuối
    
    # Chuyển đổi sang tọa độ nguyên (làm tròn để khớp với ô lưới)
    start_x, start_y = int(round(x1)), int(round(y1)) # Tọa độ nguyên điểm đầu
    end_x, end_y = int(round(x2)), int(round(y2)) # Tọa độ nguyên điểm cuối
    
    x1, y1 = start_x, start_y # Gán lại x1, y1 để bắt đầu chạy thuật toán
    x2, y2 = end_x, end_y # Gán lại x2, y2 để làm đích đến
    
    dx = abs(x2 - x1) # Tính khoảng cách tuyệt đối theo trục x
    dy = abs(y2 - y1) # Tính khoảng cách tuyệt đối theo trục y
    sx = 1 if x1 < x2 else -1 # Xác định hướng di chuyển theo trục x (1: tăng, -1: giảm)
    sy = 1 if y1 < y2 else -1 # Xác định hướng di chuyển theo trục y (1: tăng, -1: giảm)
    err = dx - dy # Khởi tạo biến lỗi cho thuật toán Bresenham
    
    mH = len(grid) # Lấy chiều cao của lưới (số hàng)
    mW = len(grid[0]) # Lấy chiều rộng của lưới (số cột)

    while True: # Vòng lặp chạy dọc theo đường thẳng nối hai điểm
        # Kiểm tra giới hạn bản đồ
        if not (0 <= x1 < mW and 0 <= y1 < mH): # Nếu điểm hiện tại nằm ngoài lưới
            return False # Trả về False (không kết nối được)

        # Kiểm tra chướng ngại vật
        # Nếu ignore_endpoints là True, bỏ qua kiểm tra tại điểm đầu và điểm cuối
        if not (ignore_endpoints and ((x1 == start_x and y1 == start_y) or (x1 == end_x and y1 == end_y))):
            if grid[y1][x1] != target_type: # Nếu ô hiện tại không phải là loại cho phép (target_type)
                return False # Trả về False (bị chặn)
            
        if x1 == x2 and y1 == y2: # Nếu đã đến điểm đích
            break # Thoát vòng lặp
            
        e2 = 2 * err # Tính biến lỗi gấp đôi để so sánh
        if e2 > -dy: # Nếu lỗi lớn hơn -dy (di chuyển theo trục x)
            err -= dy # Cập nhật lỗi
            x1 += sx # Di chuyển x thêm 1 bước theo hướng sx
        if e2 < dx: # Nếu lỗi nhỏ hơn dx (di chuyển theo trục y)
            err += dx # Cập nhật lỗi
            y1 += sy # Di chuyển y thêm 1 bước theo hướng sy
    
    return True # Nếu chạy hết vòng lặp mà không bị chặn, trả về True

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
        if attitude < 5.0: # Tăng khoảng cách tối thiểu giữa các node (ví dụ: 5.0)
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
        visible_neighbors = []
        for point2 in points:
            if point1 == point2:
                continue
            
            # Tối ưu hóa: Chỉ kiểm tra các điểm trong bán kính nhất định
            dist_sq = (point1[0] - point2[0])**2 + (point1[1] - point2[1])**2
            if dist_sq > 400: # Bán kính 20
                continue

            # Kiểm tra kết nối qua FLOOR (bỏ qua điểm đầu/cuối là WALL)
            if can_2_points_connect(grid, point1, point2, target_type=FLOOR, ignore_endpoints=True):
                visible_neighbors.append(point2)
        
        # Sắp xếp theo khoảng cách để lấy các điểm gần nhất
        visible_neighbors.sort(key=lambda p: (p[0] - point1[0])**2 + (p[1] - point1[1])**2)
        
        # Lấy tối đa 3 hàng xóm gần nhất để tạo thành tứ giác (4 điểm) hoặc tam giác (3 điểm)
        neighbors = [point1] + visible_neighbors[:3]
        
        if len(neighbors) < 3:
            continue

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

def write_city_edges_to_xml(grid, pos_map, output_path, min_angle=30 , numLanes=4, carSpeed=13.9, pedSpeed=1.4):
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
    nodes_info = list(pos_map.values())
    
    # 1. Thu thập tất cả các cạnh tiềm năng
    all_candidates = []
    for sx, sy, sid in nodes_info:
        for tx, ty, tid in nodes_info:
            if sid == tid:
                continue
            if can_2_points_connect(grid, (sx, sy), (tx, ty), target_type=FLOOR):
                dx = tx - sx
                dy = ty - sy
                dist_sq = dx*dx + dy*dy
                angle = math.atan2(dy, dx) * 180 / math.pi
                all_candidates.append({
                    'sid': sid, 'sx': sx, 'sy': sy,
                    'tid': tid, 'tx': tx, 'ty': ty,
                    'dist_sq': dist_sq,
                    'angle': angle
                })
    
    # 2. Sắp xếp theo độ dài (ưu tiên cạnh ngắn hơn)
    all_candidates.sort(key=lambda x: x['dist_sq'])
    
    final_edges = []
    
    def ccw(A, B, C):
        return (C[1]-A[1]) * (B[0]-A[0]) > (B[1]-A[1]) * (C[0]-A[0])
        
    def intersect(A, B, C, D):
        return ccw(A, C, D) != ccw(B, C, D) and ccw(A, B, C) != ccw(A, B, D)

    for cand in all_candidates:
        p1 = (cand['sx'], cand['sy'])
        p2 = (cand['tx'], cand['ty'])
        
        # Kiểm tra giao cắt với các cạnh đã chọn
        is_intersecting = False
        for exist in final_edges:
            p3 = (exist['sx'], exist['sy'])
            p4 = (exist['tx'], exist['ty'])
            
            # Bỏ qua nếu chung đỉnh (cho phép chung đỉnh đầu/cuối)
            if p1 == p3 or p1 == p4 or p2 == p3 or p2 == p4:
                continue
            
            if intersect(p1, p2, p3, p4):
                is_intersecting = True
                break
        
        if is_intersecting:
            continue
            
        # Kiểm tra góc tối thiểu tại node nguồn
        is_angle_ok = True
        for exist in final_edges:
            if exist['sid'] == cand['sid']:
                diff = abs(cand['angle'] - exist['angle'])
                diff = min(diff, 360 - diff)
                if diff < min_angle:
                    is_angle_ok = False
                    break
        
        if not is_angle_ok:
            continue
            
        final_edges.append(cand)
        
    edges_to_write = [(e['sid'], e['tid']) for e in final_edges]
    write_to_xml.write_edges_to_xml(edges_to_write, output_path, has_ped_lane=True, numLanes=numLanes, carSpeed=carSpeed, pedSpeed=pedSpeed)
    
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

    mH = len(grid)
    mW = len(grid[0])
    
    # Lấy danh sách các điểm hợp lệ
    valid_points = get_valid_points(grid, mW, mH)

    fig, ax = plt.subplots(figsize=(10, 10))
    
    # Hiển thị grid nền: 0 (FLOOR) -> Trắng, 1 (WALL) -> Đen
    # cmap='Greys' maps 0 to White, 1 to Black by default? 
    # Actually Greys: 0 is White, 1 is Black? Let's check.
    # Usually 0 is white in grayscale images.
    # If we want WALL (Black), we should map WALL to 1?
    # Let's assume 0=White, 1=Black.
    grid_display = np.array([[0 if cell == FLOOR else 1 for cell in row] for row in grid])
    # cmap='Greys' maps low to white, high to black. So 0->White, 1->Black. Correct.
    ax.imshow(grid_display, cmap='Greys', origin='lower')

    # Vẽ các điểm hợp lệ (xanh lá)
    if valid_points:
        vp_x = [p[0] for p in valid_points]
        vp_y = [p[1] for p in valid_points]
        ax.scatter(vp_x, vp_y, c='lime', s=10, label='Valid Points', zorder=4, alpha=0.6)

    nodes = list(pos_map.values())
    positions = {node[2]: (node[0], node[1]) for node in nodes}

    # Vẽ các node (xanh lục - ở đây dùng màu teal/đậm hơn để phân biệt)
    x_coords = [pos[0] for pos in positions.values()]
    y_coords = [pos[1] for pos in positions.values()]
    ax.scatter(x_coords, y_coords, c='green', s=50, label='Nodes', zorder=5)

    # Ghi nhãn cho các node
    for node_id, (x, y) in positions.items():
        ax.text(x + 0.5, y + 0.5, node_id, fontsize=9, ha='center', color='blue')

    # Vẽ các cạnh kết nối
    for sx, sy, sid in nodes:
        for tx, ty, tid in nodes:
            if sid == tid:
                continue
            if can_2_points_connect(grid, (sx, sy), (tx, ty), target_type=FLOOR):
                ax.plot([sx, tx], [sy, ty], 'b-', lw=1)

    ax.set_title("Sơ đồ các Node và kết nối")
    ax.set_xlabel("Tọa độ X")
    ax.set_ylabel("Tọa độ Y")
    ax.legend()
    plt.grid(True)
    plt.show()

def create_map(city_path, numLanes=8, carSpeed=13.9, pedSpeed=1.4):
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
        return False
    
    pos_map = get_node_position_list(grid, mW, mH)
    visualize_nodes(grid, pos_map) # Hiển thị đồ thị
    _nod_xml_path = "SUMO_xml/HelloWorld.nod.xml"
    _edg_xml_path = "SUMO_xml/HelloWorld.edg.xml"
    _net_xml_path = "SUMO_xml/HelloWorld.net.xml"
    _con_xml_path = "SUMO_xml/HelloWorld.con.xml"
    # _nod_xml_path = "./HelloWorld.nod.xml"
    # _edg_xml_path = "./HelloWorld.edg.xml"
    # _net_xml_path = "./HelloWorld.net.xml"
    # _con_xml_path = "./HelloWorld.con.xml"

     # Ghi file .nod.xml và .edg.xml
    write_to_xml.write_nodes_to_xml(pos_map, _nod_xml_path)
    write_city_edges_to_xml(grid, pos_map, _edg_xml_path, min_angle=45, numLanes=numLanes, carSpeed=carSpeed, pedSpeed=pedSpeed)
    # Tạo crossings (.con.xml) từ .nod.xml và .edg.xml (dùng width mặc định trong hàm)
    write_to_xml.write_crossings_to_con_xml(_nod_xml_path, _edg_xml_path, _con_xml_path)
    os.system(f"netconvert -n {_nod_xml_path} -e {_edg_xml_path} -x {_con_xml_path} -o {_net_xml_path} --offset.x 0 --offset.y 0")
    print(f"\n✅ Bản đồ SUMO đã được tạo thành công tại: {_net_xml_path}\n")
    return True

if __name__ == "__main__":
    # Ví dụ sử dụng
    city_map_path = "../Boston_0_256.map"  # Đường dẫn tệp bản đồ thành phố
    create_map(city_map_path, numLanes=8, carSpeed=13.9, pedSpeed=1.4)