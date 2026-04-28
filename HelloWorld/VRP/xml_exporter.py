import xml.etree.ElementTree as ET
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from staff import Staff
    from network_graph import NetworkGraph

def export_to_rou_xml(staff_list: List['Staff'], graph: 'NetworkGraph', output_file: str) -> None:
    routes_root = ET.Element("routes")
    
    for staff in staff_list:
        route_nodes = staff.get_route()
        full_edge_route = []
        
        # Nối tất cả các chuỗi cạnh từ điểm này qua điểm khác
        for i in range(len(route_nodes) - 1):
            source = route_nodes[i]
            target = route_nodes[i + 1]
            edges_path = graph.get_shortest_path_edges(source, target)
            full_edge_route.extend(edges_path)
            
        if full_edge_route:
            # Thay thế vehicle bằng flow: Xuất phát từ 0, kết thúc 3600, mỗi xe cách nhau 45s
            flow = ET.SubElement(routes_root, "flow")
            flow.set("id", f"staff_{staff.get_id()}")
            flow.set("begin", "0")
            flow.set("end", "3600")
            flow.set("period", "45")
            
            route_elem = ET.SubElement(flow, "route")
            route_elem.set("edges", " ".join(full_edge_route))
            
    tree = ET.ElementTree(routes_root)
    # Định dạng đẹp cho file XML (nếu dùng Python 3.9+)
    if hasattr(ET, "indent"):
        ET.indent(tree, space="    ", level=0)
    tree.write(output_file, encoding="UTF-8", xml_declaration=True)
    print(f"Đã xuất lộ trình ra file: {output_file}")
