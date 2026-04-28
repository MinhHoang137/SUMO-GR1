from location import Location
from network_graph import NetworkGraph

class Client(Location):
    def __init__(self, loc_id: str, graph: NetworkGraph, d: float) -> None:
        super().__init__(loc_id, graph)
        self.duration = d
