from typing import List, Optional, Dict
from company import Company
from client import Client
from .staff import Staff
from .location import Location

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
