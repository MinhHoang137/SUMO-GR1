import heapq
import math

import sumolib
import traci


def _astar_find_path(graph, start_edge_id: str, end_edge_id: str):
    """A* trên graph đơn giản (dict), chạy single-process.

    graph format: {edge_id: {'pos': (x,y), 'outgoing': [(next_edge_id, cost), ...]}}
    Returns: list[edge_id] | None
    """
    if start_edge_id not in graph or end_edge_id not in graph:
        return None

    def heuristic(id_a: str, id_b: str) -> float:
        pos_a = graph[id_a]['pos']
        pos_b = graph[id_b]['pos']
        return math.sqrt((pos_a[0] - pos_b[0])**2 + (pos_a[1] - pos_b[1])**2)

    open_set = []
    heapq.heappush(open_set, (0.0, start_edge_id))
    came_from = {}
    g_score = {start_edge_id: 0.0}

    while open_set:
        _, current_id = heapq.heappop(open_set)
        if current_id == end_edge_id:
            path = [current_id]
            while current_id in came_from:
                current_id = came_from[current_id]
                path.append(current_id)
            return path[::-1]

        current_node = graph[current_id]
        for neighbor_id, cost in current_node['outgoing']:
            tentative_g = g_score[current_id] + float(cost)
            if neighbor_id not in g_score or tentative_g < g_score[neighbor_id]:
                came_from[neighbor_id] = current_id
                g_score[neighbor_id] = tentative_g
                f = tentative_g + heuristic(neighbor_id, end_edge_id)
                heapq.heappush(open_set, (f, neighbor_id))

    return None


class CustomNavigator:
    def __init__(self, net_file: str, enable_parallel: bool = False, max_workers=None):
        """Custom A* navigation on SUMO net.

        - Default is single-process (safe on Windows).
        - If enable_parallel=True, it will create a ProcessPoolExecutor and allow batch routing.
        """
        self.net = sumolib.net.readNet(net_file)
        self.net_file = net_file
        print(f"Loaded network from {net_file}")

        self.simple_graph = self._build_simple_graph()

        self.executor = None
        if enable_parallel:
            from concurrent.futures import ProcessPoolExecutor

            # Windows: multiprocessing uses spawn; keep init minimal and avoid side-effects.
            # We pass graph once to each worker via initializer.
            self.executor = ProcessPoolExecutor(
                max_workers=max_workers,
                initializer=_init_worker,
                initargs=(self.simple_graph,),
            )

    def _build_simple_graph(self):
        """Tạo graph dạng dict {edge_id: {'pos': (x,y), 'outgoing': [(next_id, cost), ...]}}"""
        graph = {}
        for edge in self.net.getEdges():
            eid = edge.getID()
            # Bỏ qua internal edges nếu không cần thiết
            if eid.startswith(":"):
                continue
                
            # Lấy tọa độ node đầu để tính heuristic
            from_node = edge.getFromNode()
            pos = from_node.getCoord()
            
            # Tính cost và danh sách cạnh nối tiếp
            # sumolib: Edge.getOutgoing() -> dict {toEdge: [Connection, ...]}
            outgoing = []
            try:
                outgoing_map = edge.getOutgoing()
            except Exception:
                outgoing_map = {}

            for next_edge, _connections in getattr(outgoing_map, 'items', lambda: [])():
                # next_edge là Edge
                try:
                    next_eid = next_edge.getID()
                except Exception:
                    continue
                if next_eid.startswith(":"):
                    continue

                # Cost = length / speed
                try:
                    cost = next_edge.getLength() / max(0.0001, next_edge.getSpeed())
                except Exception:
                    cost = 1.0
                outgoing.append((next_eid, cost))
            
            graph[eid] = {
                'pos': pos,
                'outgoing': outgoing
            }
        return graph

    def find_path(self, start_edge_id, end_edge_id):
        """Tìm đường đơn lẻ.

        Nếu bật parallel thì chạy trong worker process; nếu không thì chạy local.
        """
        if self.executor is None:
            return _astar_find_path(self.simple_graph, start_edge_id, end_edge_id)

        future = self.executor.submit(_worker_find_path, (start_edge_id, end_edge_id))
        return future.result()

    def find_paths_batch(self, request_list):
        """
        Tìm đường cho nhiều cặp (start, end) cùng lúc.
        request_list: [(start1, end1), (start2, end2), ...]
        Returns: list of paths (hoặc None nếu không tìm thấy)
        """
        if self.executor is None:
            return [_astar_find_path(self.simple_graph, s, t) for (s, t) in request_list]

        return list(self.executor.map(_worker_find_path, request_list))

    def set_vehicle_route(self, veh_id, start_edge, end_edge):
        path = self.find_path(start_edge, end_edge)
        if path:
            try:
                traci.vehicle.setRoute(veh_id, path)
                return True
            except traci.TraCIException as e:
                print(f"Error setting route for {veh_id}: {e}")
        return False

    def set_vehicle_routes_batch(self, veh_data_list):
        """
        Xử lý hàng loạt xe.
        veh_data_list: [(veh_id, start_edge, end_edge), ...]
        """
        requests = [(start, end) for _, start, end in veh_data_list]
        paths = self.find_paths_batch(requests)
        
        for (veh_id, _, _), path in zip(veh_data_list, paths):
            if path:
                try:
                    traci.vehicle.setRoute(veh_id, path)
                except Exception as e:
                    print(f"Error setting route for {veh_id}: {e}")

    def close(self):
        if self.executor is not None:
            self.executor.shutdown()


# --- multiprocessing worker support (optional) ---
_worker_graph = None


def _init_worker(graph_data):
    global _worker_graph
    _worker_graph = graph_data


def _worker_find_path(args):
    start_edge_id, end_edge_id = args
    return _astar_find_path(_worker_graph, start_edge_id, end_edge_id)

# Ví dụ sử dụng (đặt trong main.py hoặc script riêng):
# navigator = CustomNavigator("SUMO_xml/HelloWorld.net.xml")
# navigator.set_vehicle_route("veh_0", "edge_1", "edge_10")
