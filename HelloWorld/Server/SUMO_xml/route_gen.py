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


def create_routes_osm(num_pairs, car_cr_type, has_ped=True, ped_cr_type="CS",
                      ped_impatience=0.5, net_xml_path="SUMO_xml/HelloWorld.net.xml"):
    """
    [DEPRECATED khỏi launcher chính] Sinh route tự động cho OSM network.

    Đã được thay thế bằng Custom Script mode (user tự dựng .rou.xml bằng netedit).
    Hàm này được giữ lại làm tham chiếu / phục vụ debug pipeline OSM cũ.

    Tạo file .rou.xml cho OSM network bằng cách pre-compute đường đi explicit.

    Lý do cần hàm này:
        - OSM network không hỗ trợ tốt TAZ routing (fromJunction/toJunction)
          do SUMO không tìm được route giữa các junction TAZ.
        - Thay vào đó: dùng NetworkGraph (Dijkstra) để tính sẵn chuỗi edges,
          rồi ghi <flow><route edges="..."/></flow> để SUMO nhận route trực tiếp.
    """
    from VRP.network_graph import NetworkGraph

    rou_path = "SUMO_xml/HelloWorld.rou.xml"

    # Đọc tất cả junction từ .net.xml để lấy vị trí (x, y)
    crossroads = CrossRoadReader.read_all_junctions()
    if not crossroads:
        print("[Warning] Không tìm thấy junction trong .net.xml.")
        return

    # Xây đồ thị để tính shortest path
    graph = NetworkGraph.from_net_xml(net_xml_path)
    # Chỉ giữ node có outgoing edges
    valid_nodes = set(n for n in graph.graph if graph.graph[n])

    # Lọc crossroads chỉ còn các junction có trong graph
    valid_crossroads = [cr for cr in crossroads if cr["i"] in valid_nodes]
    if len(valid_crossroads) < 2:
        print("[Warning] Không đủ junction hợp lệ để tạo route.")
        return

    # Tạo cặp (start, end) theo car_cr_type
    def _make_pairs(cr_type, crs, n):
        if cr_type == "CS":
            return cross_side_gen(crs, n)
        elif cr_type == "SS":
            return swap_side_gen(crs, n)
        elif cr_type == "IO":
            return in_out_gen(crs, n)
        elif cr_type == "OI":
            return out_in_gen(crs, n)
        return cross_side_gen(crs, n)

    car_starts, car_ends = _make_pairs(car_cr_type, valid_crossroads, num_pairs)

    # Root XML
    routes_root = ET.Element("routes", {
        "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
        "xsi:noNamespaceSchemaLocation": "http://sumo.dlr.de/xsd/routes_file.xsd",
    })
    # vType cho xe
    ET.SubElement(routes_root, "vType", {"id": "car", "vClass": "passenger"})

    written_cars = 0
    for i, (s, e) in enumerate(zip(car_starts, car_ends)):
        s_id = s["i"]
        e_id = e["i"]
        edges = graph.get_shortest_path_edges(s_id, e_id)
        if not edges:
            continue
        flow = ET.SubElement(routes_root, "flow", {
            "id": f"f_{i}",
            "type": "car",
            "begin": "0.00",
            "end": "3600.00",
            "period": "30.00",
            "departLane": "best",
            "departSpeed": "max",
        })
        ET.SubElement(flow, "route", {"edges": " ".join(edges)})
        written_cars += 1

    print(f"✅ Đã tạo {written_cars} car flow cho OSM.")

    # Người đi bộ dùng personTrip fromJunction/toJunction
    # (personTrip hỗ trợ teleport nên ít bị lỗi hơn vehicle flow)
    if has_ped:
        imp = max(0.0, min(1.0, float(ped_impatience)))
        vtype_id = f"ped_{imp:.2f}".replace(".", "_")
        ET.SubElement(routes_root, "vType", {
            "id": vtype_id, "vClass": "pedestrian", "impatience": f"{imp:.2f}"
        })
        ped_starts, ped_ends = _make_pairs(ped_cr_type, valid_crossroads, num_pairs)
        written_peds = 0
        for i, (s, e) in enumerate(zip(ped_starts, ped_ends)):
            pf = ET.SubElement(routes_root, "personFlow", {
                "id": f"pf_{i}", "type": vtype_id,
                "begin": "0.00", "end": "3600.00", "period": "30.00",
            })
            ET.SubElement(pf, "personTrip", {
                "fromJunction": s["i"], "toJunction": e["i"]
            })
            written_peds += 1
        print(f"✅ Đã tạo {written_peds} personFlow (người đi bộ) cho OSM.")

    # Ghi file
    tree = ET.ElementTree(routes_root)
    if hasattr(ET, "indent"):
        ET.indent(tree, space="    ", level=0)
    os.makedirs(os.path.dirname(rou_path), exist_ok=True) if os.path.dirname(rou_path) else None
    tree.write(rou_path, encoding="UTF-8", xml_declaration=True)
    print(f"✅ Route file đã ghi: {rou_path}")



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
        x, y = cr["p"][0], cr["p"][1]  # cr["p"] có thể là [x,y] hoặc [x,y,z] (junction 3D)
        center_x += x
        center_y += y
    center_x /= len(crossroads)
    center_y /= len(crossroads)
    for cr in crossroads:
        x, y = cr["p"][0], cr["p"][1]  # cr["p"] có thể là [x,y] hoặc [x,y,z] (junction 3D)
        median_rad += ((x - center_x) ** 2 + (y - center_y) ** 2) ** 0.5
    median_rad /= len(crossroads)
    for cr in crossroads:
        x, y = cr["p"][0], cr["p"][1]  # cr["p"] có thể là [x,y] hoặc [x,y,z] (junction 3D)
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

def create_routes(num_pairs, car_cr_type, has_ped=True, ped_cr_type="CS", ped_impatience=0.5,
                  edge_file_path=None):
    """
    Tạo file .rou.xml chứa các tuyến đường cho xe và người đi bộ dựa trên loại phân chia nút giao thông.
    Args:
        num_pairs (int): Số lượng cặp nút giao thông cần tạo.
        car_cr_type (str): Loại phân chia nút giao thông cho xe. Giá trị có thể là "CS", "SS", "IO", "OI".
        has_ped (bool): Có tạo tuyến đường cho người đi bộ hay không.
        ped_cr_type (str): Loại phân chia nút giao thông cho người đi bộ. Giá trị có thể là "CS", "SS", "IO", "OI".
        ped_impatience (float): Mức độ thiếu kiên nhẫn của người đi bộ (0.0 đến 1.0).
        edge_file_path (str|None): File dùng để kiểm tra tính khả thi của tuyến đường.
            - Mặc định (None): dùng HelloWorld.edg.xml (maze mode).
            - Truyền HelloWorld.net.xml khi dùng OSM để lấy đúng junction IDs.
    """
    CS = "CS"
    SS = "SS"
    IO = "IO"
    OI = "OI"
    rou_path = "SUMO_xml/HelloWorld.rou.xml"
    # Nếu không truyền, dùng .edg.xml mặc định (maze mode)
    _edge_path = edge_file_path if edge_file_path else "SUMO_xml/HelloWorld.edg.xml"
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
    write_to_xml.write_car_route_to_xml(start_list, end_list, rou_path, edge_file_path=_edge_path)
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
        write_to_xml.write_ped_route_to_xml(start_list, end_list, rou_path, impatience=ped_impatience, edge_file_path=_edge_path)
    


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
