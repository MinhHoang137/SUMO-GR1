import os
import xml.etree.ElementTree as ET
from datetime import datetime
from network_graph import NetworkGraph
from company import Company
from client import Client
from staff import Staff
from controller import Controller
from xml_exporter import export_to_rou_xml

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    node_file = os.path.join(base_dir, "..", "SUMO_xml", "HelloWorld.nod.xml")
    edge_file = os.path.join(base_dir, "..", "SUMO_xml", "HelloWorld.edg.xml")
    
    print(f"Reading graph from:\n{node_file}\n{edge_file}")
    graph = NetworkGraph(node_file, edge_file)
    print(f"Graph loaded with {len(graph.graph)} nodes.")
    
    if len(graph.graph) == 0:
        print("Lỗi: Không tìm thấy node nào trong đồ thị. Vui lòng kiểm tra lại file XML.")
        return

    nodes_list = list(graph.graph.keys())
    company_node = nodes_list[0]
    start_point = Company(company_node, graph)
    
    client_nodes = nodes_list[1:min(10, len(nodes_list))]
    all_clients = []
    
    for node_id in client_nodes:
        all_clients.append(Client(node_id, graph, 10.0))
        
    K = 3 
    my_staff = []
    for i in range(K):
        my_staff.append(Staff(i + 1, start_point))
        
    print(f"Khởi tạo xong: 1 Công ty ({company_node}), {len(all_clients)} Khách hàng, {K} Nhân viên.")
    
    assignment = Controller()
    print("Đang chạy thuật toán base_case...")
    assignment.base_case(start_point, all_clients, my_staff)
    
    print("Đang chạy thuật toán swap_case...")
    assignment.swap_case(start_point, all_clients, my_staff)
    
    print(f"\nKết quả lộ trình cho {K} nhân viên:")
    for staff in my_staff:
        print(f"Nhân viên {staff.get_id()} - Tổng chi phí (quãng đường): {staff.get_total_route():.2f}")
        print(f"Số điểm đi qua: {len(staff.get_route())}")
        print(f"Lộ trình: {' -> '.join(staff.get_route())}")

    # Gọi hàm xuất route ra file .rou.xml
    output_xml = os.path.join(base_dir, "..", "SUMO_xml", "VRP_output.rou.xml")
    export_to_rou_xml(my_staff, graph, output_xml)

if __name__ == '__main__':
    main()
