from typing import List, Dict
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
