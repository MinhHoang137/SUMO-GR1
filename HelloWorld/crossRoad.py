import os
import json
import xml.etree.ElementTree as ET
from math import atan2

# Đường dẫn đến file .net.xml
NET_XML_PATH = os.path.join(os.path.dirname(__file__), 'HelloWorld.net.xml')
# Đường dẫn đến file JSON đầu ra
OUTPUT_FILE = './TestGR1.1/Assets/Scripts/SumoData/CrossRoad.json'


def parse_shape(shape):
    """Chuyển chuỗi shape thành danh sách các cặp tọa độ (x, y)."""
    points = shape.strip().split(' ')
    vertices = [(float(p.split(',')[0]), float(p.split(',')[1])) for p in points]
    return vertices


def sort_clockwise(vertices):
    """Sắp xếp các đỉnh theo chiều kim đồng hồ."""
    if not vertices:
        return []

    # Tính trọng tâm của các đỉnh
    center_x = sum(v[0] for v in vertices) / len(vertices)
    center_y = sum(v[1] for v in vertices) / len(vertices)

    # Sắp xếp theo góc từ trọng tâm
    sorted_vertices = sorted(vertices, key=lambda v: atan2(v[1] - center_y, v[0] - center_x), reverse=True)
    return sorted_vertices


def read_all_junctions():
    if not os.path.exists(NET_XML_PATH):
        print(f"Error: {NET_XML_PATH} does not exist.")
        return

    tree = ET.parse(NET_XML_PATH)
    root = tree.getroot()

    crossroads = []  # Danh sách các ngã tư

    for junction in root.findall('junction'):
        junction_id = junction.get('id')
        junction_type = junction.get('type', 'unknown')  # Nếu không có type thì để là 'unknown'
        x = float(junction.get('x'))
        y = float(junction.get('y'))
        shape = junction.get('shape')

        if shape:
            vertices = parse_shape(shape)
            sorted_vertices = sort_clockwise(vertices)

            # Định dạng theo cấu trúc C# yêu cầu
            crossroad = {
                "id": junction_id,
                "type": junction_type,  # Thêm thông tin loại junction
                "position": [x, y],
                "vertices": [{"x": v[0], "y": v[1]} for v in sorted_vertices]
            }
            crossroads.append(crossroad)

    if crossroads:
        # Ghi file JSON theo cấu trúc C# yêu cầu (UTF-8 không BOM)
        with open(OUTPUT_FILE, 'w', encoding='utf-8-sig') as f:
            json.dump(crossroads, f, indent=4, ensure_ascii=False)
        print(f"Junctions data saved to {OUTPUT_FILE}")
    else:
        print("No junctions found in the file.")


if __name__ == "__main__":
    read_all_junctions()
