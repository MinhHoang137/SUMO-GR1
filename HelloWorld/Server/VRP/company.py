from location import Location
from network_graph import NetworkGraph

class Company(Location):
    def __init__(self, loc_id: str, graph: NetworkGraph) -> None:
        super().__init__(loc_id, graph)
        self.duration = 0.0
