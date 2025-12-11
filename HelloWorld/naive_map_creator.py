import os
from SUMO_xml import write_to_xml
from SUMO_xml.create_map_from_maze import write_maze_edges_to_xml

WALL = '@'
FLOOR = '.'
def fl_str(number: float) -> str:
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
    
def get_node_pos_map(grid, width, height):
    """
    Tạo bản đồ vị trí các node từ ma trận bản đồ.
    
    Tham số:
        grid: Mảng 2 chiều đại diện cho bản đồ.
        width: Chiều rộng của bản đồ.
        height: Chiều cao của bản đồ.
        
    Trả về:
        Một từ điển (dictionary) ánh xạ 'key' của node
        sang tọa độ (x, y) và ID của node.
    """
    pos_map = {}
    node_id = 0
    
    for y in range(height):
        for x in range(width):
            if grid[y][x] == FLOOR:  # Giả sử 'N' đại diện cho node
                key = f"{fl_str(x)}_{fl_str(y)}"
                pos_map[key] = (x, y, f"n_{node_id}")
                node_id += 1
                
    return pos_map

def naive_create_map_files(input_map_path, output_nod_path, output_edge_path, output_con_path, numLanes=8):
    """
    Tạo tệp .net.xml và .edg.xml từ tệp .map đơn giản.
    
    Args:
        input_map_path (str): Đường dẫn tới tệp .map đầu vào.
        output_nod_path (str): Đường dẫn tới tệp .nod.xml đầu ra.
        output_edge_path (str): Đường dẫn tới tệp .edg.xml đầu ra.
        output_con_path (str): Đường dẫn tới tệp .con.xml đầu ra.
        numLanes (int): Số làn cho mỗi cạnh.
    """
    grid, width, height = parse_map_file(input_map_path)
    
    if grid is None:
        print("Không thể tạo bản đồ do lỗi đọc tệp .map.")
        return
    
    pos_map = get_node_pos_map(grid, width, height)
    
    write_to_xml.write_nodes_to_xml(pos_map, output_nod_path, scale=40.0)
    write_maze_edges_to_xml(grid, pos_map, height, width, output_edge_path, numLanes = numLanes)
    write_to_xml.write_crossings_to_con_xml(output_nod_path, output_edge_path, output_con_path)
    print("Đã tạo tệp .nod.xml, .edg.xml và .con.xml thành công.")

def naive_create_map(maze_file_path, num_lanes):
    """
    Tạo bản đồ SUMO từ tệp mê cung và lưu các tệp cần thiết.
    
    Tham số:
        maze_file_path: Đường dẫn tới tệp mê cung (.map).
        num_lanes: Số làn cho mỗi cạnh.
    """
    output_nod_path = "SUMO_xml/HelloWorld.nod.xml"
    output_edge_path = "SUMO_xml/HelloWorld.edg.xml"
    output_con_path = "SUMO_xml/HelloWorld.con.xml"
    net_path = "SUMO_xml/HelloWorld.net.xml"

    naive_create_map_files(maze_file_path, output_nod_path, output_edge_path, output_con_path, num_lanes)
    os.system(f"netconvert -n {output_nod_path} -e {output_edge_path} -x {output_con_path} -o {net_path} --offset.x 0 --offset.y 0")
    print(f"Tệp bản đồ đã được lưu tại:\n- {output_nod_path}\n- {output_edge_path}\n- {output_con_path}\n- {net_path}")

# if __name__ == "__main__":
#     map_file_path = "maze-32-32-4.map"
#     num_lanes = 4

#     create_map_from_maze_file(map_file_path, num_lanes)
