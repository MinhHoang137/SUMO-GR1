import os

folder = r'd:/program/SUMO-GR1-3rdWeek/HelloWorld/VRP'
files = {
    'location.py': '''from typing import Union
from network_graph import NetworkGraph

class Location:
    def __init__(self, loc_id: str, graph: NetworkGraph) -> None:
        self.id: str = loc_id
        self.duration: float = 0.0
        self.graph: NetworkGraph = graph
    
    def get_id(self) -> str:
        return self.id
        
    def get_duration(self) -> float:
        return self.duration
        
    def get_enter_cost(self, target_id: str) -> float:
        return self.graph.get_shortest_path_cost(self.id, target_id)
''',
    'client.py': '''from location import Location
from network_graph import NetworkGraph

class Client(Location):
    def __init__(self, loc_id: str, graph: NetworkGraph, d: float) -> None:
        super().__init__(loc_id, graph)
        self.duration = d
''',
    'company.py': '''from location import Location
from network_graph import NetworkGraph

class Company(Location):
    def __init__(self, loc_id: str, graph: NetworkGraph) -> None:
        super().__init__(loc_id, graph)
        self.duration = 0.0
''',
    'staff.py': '''from typing import List, Dict
from location import Location
from company import Company

class Staff:
    def __init__(self, staff_id: int, start: Company) -> None:
        self.id: int = staff_id
        self.route: List[str] = [start.get_id()]
        self.total_up_to: List[float] = []
        self.total_at: List[float] = []
        self.total_route: float = 0.0
        self.current_location: Location = start
        
    def go_to(self, t: Location) -> None:
        cost = self.current_location.get_enter_cost(t.get_id())
        self.total_up_to.append(self.total_route + cost)
        self.total_at.append(self.total_route)
        self.total_route += cost + t.get_duration()
        self.route.append(t.get_id())
        self.current_location = t
        
    def get_id(self) -> int:
        return self.id
        
    def get_route(self) -> List[str]:
        return self.route
        
    def get_total_route(self) -> float:
        return self.total_route
        
    def get_current_location(self) -> Location:
        return self.current_location
        
    def get_total_up_to(self) -> List[float]:
        return self.total_up_to
        
    def get_total_at(self) -> List[float]:
        return self.total_at
        
    def update_total_up_to(self, start_point: Company, loc_map: Dict[str, Location]) -> None:
        current = 1
        self.total_up_to.clear()
        self.total_at.clear()
        if len(self.route) <= 1:
            self.total_route = 0.0
            return
            
        first_cost = start_point.get_enter_cost(self.route[1])
        self.total_up_to.append(first_cost)
        self.total_at.append(0.0)
        
        while current < len(self.route) - 1:
            current_loc = loc_map[self.route[current]]
            next_loc = loc_map[self.route[current + 1]]
            
            self.total_at.append(self.total_up_to[current - 1] + current_loc.get_duration())
            self.total_up_to.append(current_loc.get_enter_cost(next_loc.get_id()) +
                                    current_loc.get_duration() +
                                    self.total_up_to[current - 1])
            current += 1
            
        self.total_route = self.total_up_to[-1] if self.total_up_to else 0.0
''',
    'controller.py': '''from typing import List, Optional, Dict
from company import Company
from client import Client
from staff import Staff
from location import Location

class Controller:
    def base_case(self, start_point: Company, all_clients: List[Client], my_staff: List[Staff]) -> None:
        remaining: List[Client] = list(all_clients)
        
        while remaining:
            for staff in my_staff:
                if not remaining:
                    break
                    
                min_cost: float = float('inf')
                found: Optional[Client] = None
                
                for client in remaining:
                    cost = staff.get_current_location().get_enter_cost(client.get_id())
                    if cost < min_cost:
                        min_cost = cost
                        found = client
                        
                if found is not None:
                    staff.go_to(found)
                    remaining.remove(found)
                
        for staff in my_staff:
            staff.go_to(start_point)
            
    def swap_case(self, start_point: Company, all_clients: List[Client], my_staff: List[Staff]) -> None:
        my_staff.sort(key=lambda x: x.get_total_route(), reverse=True)
        min_val: float = my_staff[0].get_total_route()
        
        remaining: List[Staff] = my_staff[1:]
        
        loc_map: Dict[str, Location] = {c.get_id(): c for c in all_clients}
        loc_map[start_point.get_id()] = start_point
        
        for i in range(1, len(my_staff[0].get_total_up_to())):
            current_cut_off = my_staff[0].get_total_at()[i]
            current_id = i
            
            for staff in remaining:
                idx = i - 1
                if idx >= len(staff.get_total_up_to()) or idx < 0:
                    continue
                cut_off = staff.get_total_route() - staff.get_total_up_to()[idx]
                
                client_a_id = my_staff[0].get_route()[current_id]
                client_a = loc_map.get(client_a_id)
                if not client_a: continue
                
                target_node_b_id = staff.get_route()[idx + 1]
                
                if current_cut_off + cut_off + client_a.get_enter_cost(target_node_b_id) < min_val:
                    min_val = current_cut_off + cut_off
                    self.swap_list(my_staff[0].get_route(), staff.get_route(), current_id, idx, my_staff[0], staff, start_point, loc_map)

    def swap_list(self, a: List[str], b: List[str], cut_off_a: int, cut_off_b: int, staff_a: Staff, staff_b: Staff, start_point: Company, loc_map: Dict[str, Location]) -> None:
        add_to_a = a[cut_off_a + 1:]
        add_to_b = b[cut_off_b + 1:]
        
        del a[cut_off_a + 1:]
        del b[cut_off_b + 1:]
        
        a.extend(add_to_b)
        b.extend(add_to_a)
        
        staff_a.update_total_up_to(start_point, loc_map)
        staff_b.update_total_up_to(start_point, loc_map)
''',
    'main.py': '''import os
from network_graph import NetworkGraph
from company import Company
from client import Client
from staff import Staff
from controller import Controller

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    node_file = os.path.join(base_dir, "..", "SUMO_xml", "HelloWorld.nod.xml")
    edge_file = os.path.join(base_dir, "..", "SUMO_xml", "HelloWorld.edg.xml")
    
    print(f"Reading graph from:\\n{node_file}\\n{edge_file}")
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
    
    print(f"\\nKết quả lộ trình cho {K} nhân viên:")
    for staff in my_staff:
        print(f"Nhân viên {staff.get_id()} - Tổng chi phí (quãng đường): {staff.get_total_route():.2f}")
        print(f"Số điểm đi qua: {len(staff.get_route())}")
        print(f"Lộ trình: {' -> '.join(staff.get_route())}")

if __name__ == '__main__':
    main()
'''
}

for filename, content in files.items():
    with open(os.path.join(folder, filename), 'w', encoding='utf-8') as f:
        f.write(content)
