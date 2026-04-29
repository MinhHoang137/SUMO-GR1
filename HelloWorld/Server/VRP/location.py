from typing import Union
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
