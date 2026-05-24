

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
        with open(filepath, 'r', encoding='utf-8') as f:
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