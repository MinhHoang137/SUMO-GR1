import random
import xml.etree.ElementTree as ET
import os
import sys

# Bổ sung đường dẫn cha để import sibling package 'Traffic'
_CUR_DIR = os.path.dirname(__file__)
_PARENT_DIR = os.path.abspath(os.path.join(_CUR_DIR, os.pardir))
if _PARENT_DIR not in sys.path:
    sys.path.insert(0, _PARENT_DIR)

from Traffic.crossRoad import CrossRoadReader  # noqa: F401
from SUMO_xml import write_to_xml

def split_side(crossroads):
    """
    Chia các nút giao thông thành hai bên trái và phải dựa trên tọa độ x.
    Args:
        crossroads (list): Danh sách các dict nút giao thông với khóa "position" chứa tọa độ [x, y].
    Returns:
        tuple: Hai danh sách, danh sách bên trái và danh sách bên phải.
    """
    left = []
    right = []
    median_x = 0
    if not crossroads:
        return left, right
    for cr in crossroads:
        median_x += cr["p"][0]
    median_x /= len(crossroads)
    for cr in crossroads:
        if cr["p"][0] < median_x:
            left.append(cr)
        else:
            right.append(cr)
    return left, right

def split_in_out(crossroads):
    """
        Chia các nút giao thông thành hai bên trong và bên ngoài dựa.
        Args:
            crossroads (list): Danh sách các dict nút giao thông với khóa "position" chứa tọa độ [x, y].
        Returns:
            tuple: Hai danh sách, danh sách bên trong và danh sách bên ngoài
        """
    _in = []
    _out = []
    median_rad = 0
    center_x = 0
    center_y = 0
    if not crossroads:
        return _in, _out
    for cr in crossroads:
        x, y = cr["p"]
        center_x += x
        center_y += y
    center_x /= len(crossroads)
    center_y /= len(crossroads)
    for cr in crossroads:
        x, y = cr["p"]
        median_rad += ((x - center_x) ** 2 + (y - center_y) ** 2) ** 0.5
    median_rad /= len(crossroads)
    for cr in crossroads:
        x, y = cr["p"]
        rad = ((x - center_x) ** 2 + (y - center_y) ** 2) ** 0.5
        if rad < median_rad:
            _in.append(cr)
        else:
            _out.append(cr)
    return _in, _out

def cross_side_gen(crossroads, num_pairs):
    """
        Chia các nút giao thông thành hai bên trái và phải dựa trên tọa độ x.
        Args:
            crossroads (list): Danh sách các dict nút giao thông với khóa "position" chứa tọa độ [x, y].
            num_pairs (int): Số lượng cặp nút giao thông cần tạo.
        Returns:
            tuple: Hai danh sách, danh sách xuất phát và danh sách kết thúc
        """
    left, right = split_side(crossroads)
    true_num_pairs = min(num_pairs, len(left), len(right))
    start = []
    end = []
    for i in range(true_num_pairs):
        upper_bound = min(true_num_pairs - 1, len(left) - 1, len(right) - 1)
        rand_i = random.randint(0, upper_bound)
        start.append(left[rand_i])
        end.append(right[rand_i])
        left.pop(rand_i)
        right.pop(rand_i)
    return start, end

def swap_side_gen(crossroads, num_pairs):
    """
        Chia các nút giao thông thành hai bên trong và ngoài dựa trên tọa độ.
        Args:
            crossroads (list): Danh sách các dict nút giao thông với khóa "position" chứa tọa độ [x, y].
            num_pairs (int): Số lượng cặp nút giao thông cần tạo.
        Returns:
            tuple: Hai danh sách, danh sách xuất phát và danh sách kết thúc
        """
    left, right = split_side(crossroads)
    true_num_pairs = min(num_pairs, len(left), len(right))
    start = []
    end = []
    for i in range(true_num_pairs):
        upper_bound = min(true_num_pairs - 1, len(left) - 1, len(right) - 1)
        rand_i = random.randint(0, upper_bound)
        if (i % 2) == 0:
            start.append(left[rand_i])
            end.append(right[rand_i])
        else:
            start.append(right[rand_i])
            end.append(left[rand_i])
        left.pop(rand_i)
        right.pop(rand_i)
    return start, end

def in_out_gen(crossroads, num_pairs):
    _in, _out = split_in_out(crossroads)
    true_num_pairs = min(num_pairs, len(_in), len(_out))
    start = []
    end = []
    for i in range(true_num_pairs):
        upper_bound = min(true_num_pairs - 1, len(_in) - 1, len(_out) - 1)
        rand_i = random.randint(0, upper_bound)
        start.append(_in[rand_i])
        end.append(_out[rand_i])
        _in.pop(rand_i)
        _out.pop(rand_i)
    return start, end

def out_in_gen(crossroads, num_pairs):
    _in, _out = split_in_out(crossroads)
    true_num_pairs = min(num_pairs, len(_in), len(_out))
    start = []
    end = []
    for i in range(true_num_pairs):
        upper_bound = min(true_num_pairs - 1, len(_in) - 1, len(_out) - 1)
        rand_i = random.randint(0, upper_bound)
        start.append(_out[rand_i])
        end.append(_in[rand_i])
        _in.pop(rand_i)
        _out.pop(rand_i)
    return start, end

def create_routes(num_pairs, car_cr_type, has_ped=True, ped_cr_type="CS", ped_impatience=0.5):
    """
    Tạo file .rou.xml chứa các tuyến đường cho xe và người đi bộ dựa trên loại phân chia nút giao thông.
    Args:
        num_pairs (int): Số lượng cặp nút giao thông cần tạo.
        car_cr_type (str): Loại phân chia nút giao thông cho xe. Giá trị có thể là "CS", "SS", "IO", "OI".
        has_ped (bool): Có tạo tuyến đường cho người đi bộ hay không.
        ped_cr_type (str): Loại phân chia nút giao thông cho người đi bộ. Giá trị có thể là "CS", "SS", "IO", "OI".
        ped_impatience (float): Mức độ thiếu kiên nhẫn của người đi bộ (0.0 đến 1.0).
    """
    CS = "CS"
    SS = "SS"
    IO = "IO"
    OI = "OI"
    rou_path = "SUMO_xml/HelloWorld.rou.xml"
    edge_path = "SUMO_xml/HelloWorld.edg.xml"
    crossroads = CrossRoadReader.read_all_junctions()
    if car_cr_type == CS:
        start_list, end_list = cross_side_gen(crossroads, num_pairs)
    elif car_cr_type == SS:
        start_list, end_list = swap_side_gen(crossroads, num_pairs)
    elif car_cr_type == IO:
        start_list, end_list = in_out_gen(crossroads, num_pairs)
    elif car_cr_type == OI:
        start_list, end_list = out_in_gen(crossroads, num_pairs)
    else:
        print(f"không xác định car_cr_type: {car_cr_type}. Sử dụng cross_side_gen làm mặc định.")
        start_list, end_list = cross_side_gen(crossroads, num_pairs)
    write_to_xml.write_car_route_to_xml(start_list, end_list, rou_path, edge_file_path=edge_path)
    if has_ped:
        if ped_cr_type == CS:
            start_list, end_list = cross_side_gen(crossroads, num_pairs)
        elif ped_cr_type == SS:
            start_list, end_list = swap_side_gen(crossroads, num_pairs)
        elif ped_cr_type == IO:
            start_list, end_list = in_out_gen(crossroads, num_pairs)
        elif ped_cr_type == OI:
            start_list, end_list = out_in_gen(crossroads, num_pairs)
        else:
            print(f"không xác định ped_cr_type: {ped_cr_type}. Sử dụng cross_side_gen làm mặc định.")
            start_list, end_list = cross_side_gen(crossroads, num_pairs)
        write_to_xml.write_ped_route_to_xml(start_list, end_list, rou_path, impatience=ped_impatience, edge_file_path=edge_path)
    


if __name__ == "__main__":
    # Ví dụ: lấy danh sách nút giao thông từ CrossRoadReader (đã có trong Traffic/crossRoad.py)
    # rồi tách cặp bằng cross_side_gen hoặc split_in_out tùy bạn
    # start_list, end_list = route_gen.cross_side_gen(crossroads, num_pairs)

    rou_path = "SUMO_xml/HelloWorld.rou.xml"
    crossroads = CrossRoadReader.read_all_junctions()
    start_list, end_list = swap_side_gen(crossroads, 10)
    write_to_xml.write_car_route_to_xml(start_list, end_list, rou_path)
    start_list, end_list = cross_side_gen(crossroads, 10)
    write_to_xml.write_ped_route_to_xml(start_list, end_list, rou_path)
