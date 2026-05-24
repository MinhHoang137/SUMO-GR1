import xml.etree.ElementTree as ET
import heapq
import math
from typing import Dict, List, Tuple

class NetworkGraph:
    def __init__(self, node_file: str, edge_file: str) -> None:
        self.graph: Dict[str, List[Tuple[str, float, str]]] = {}
        self.distance_cache: Dict[str, Dict[str, float]] = {}
        self.path_cache: Dict[str, Dict[str, List[str]]] = {}
        self.nodes_pos: Dict[str, Tuple[float, float]] = {}
        self._build_graph(node_file, edge_file)

    @classmethod
    def from_net_xml(cls, net_file: str) -> "NetworkGraph":
        """Tạo NetworkGraph trực tiếp từ tệp .net.xml của SUMO.
        
        Thay thế cho __init__(node_file, edge_file) khi chỉ có tệp .net.xml
        (ví dụ: sau khi chuyển đổi từ OSM bằng netconvert).
        
        Cấu trúc .net.xml:
        - <junction id="..." x="..." y="..." type="..."/> → node
        - <edge id="..." from="..." to="..."><lane speed="..." length="..."/></edge> → edge
        Các edge nội bộ (id bắt đầu bằng ':') bị bỏ qua.
        """
        instance = cls.__new__(cls)
        instance.graph = {}
        instance.distance_cache = {}
        instance.path_cache = {}
        instance.nodes_pos = {}
        instance._build_graph_from_net(net_file)
        return instance

    def _build_graph_from_net(self, net_file: str) -> None:
        try:
            tree = ET.parse(net_file)
            root = tree.getroot()
        except Exception as e:
            print(f"Warning: Could not parse net file {net_file}: {e}")
            return

        # --- Đọc junction làm node ---
        SKIP_TYPES = {"internal", "dead_end"}
        for junc in root.findall("junction"):
            junc_id = junc.get("id")
            junc_type = junc.get("type", "")
            if not junc_id or junc_type in SKIP_TYPES:
                continue
            x = float(junc.get("x", 0.0))
            y = float(junc.get("y", 0.0))
            self.nodes_pos[junc_id] = (x, y)
            if junc_id not in self.graph:
                self.graph[junc_id] = []
                self.distance_cache[junc_id] = {}
                self.path_cache[junc_id] = {}

        # --- Đọc edge ---
        for edge in root.findall("edge"):
            edge_id = edge.get("id", "")
            if edge_id.startswith(":"):
                # Bỏ qua edge nội bộ junction
                continue
            from_node = edge.get("from")
            to_node = edge.get("to")
            if not from_node or not to_node:
                continue

            # Lấy tốc độ và độ dài từ lane đầu tiên
            speeds = []
            lengths = []
            for lane in edge.findall("lane"):
                if lane.get("speed"):
                    speeds.append(float(lane.get("speed")))
                if lane.get("length"):
                    lengths.append(float(lane.get("length")))

            speed = max(speeds) if speeds else 13.9
            if lengths:
                length = max(lengths)
            else:
                x1, y1 = self.nodes_pos.get(from_node, (0.0, 0.0))
                x2, y2 = self.nodes_pos.get(to_node, (0.0, 0.0))
                length = math.hypot(x2 - x1, y2 - y1)

            weight = length / speed if speed > 0 else float("inf")

            for nid in (from_node, to_node):
                if nid not in self.graph:
                    self.graph[nid] = []
                    self.distance_cache[nid] = {}
                    self.path_cache[nid] = {}

            self.graph[from_node].append((to_node, weight, edge_id))

    def _build_graph(self, node_file: str, edge_file: str) -> None:
        try:
            tree_nodes = ET.parse(node_file)
            root_nodes = tree_nodes.getroot()
            for node in root_nodes.findall('node'):
                node_id = node.get('id')
                if node_id:
                    self.graph[node_id] = []
                    self.distance_cache[node_id] = {}
                    self.path_cache[node_id] = {}
                    
                    x = float(node.get('x', 0.0))
                    y = float(node.get('y', 0.0))
                    self.nodes_pos[node_id] = (x, y)
        except Exception as e:
            print(f"Warning: Could not parse node file {node_file}: {e}")

        try:
            tree_edges = ET.parse(edge_file)
            root_edges = tree_edges.getroot()
            for edge in root_edges.findall('edge'):
                from_node = edge.get('from')
                to_node = edge.get('to')
                edge_id = edge.get('id')
                if not from_node or not to_node or not edge_id:
                    continue
                
                # Fetch lane speeds if available
                speeds = []
                if edge.get('speed'):
                    speeds.append(float(edge.get('speed')))
                for lane in edge.findall('lane'):
                    if lane.get('speed'):
                        speeds.append(float(lane.get('speed')))
                
                # Use max speed (or a default if not specified)
                speed = max(speeds) if speeds else 13.9
                
                # Assume length is specified, otherwise calculate distance from nodes
                if edge.get('length'):
                    length = float(edge.get('length'))
                else:
                    x1, y1 = self.nodes_pos.get(from_node, (0.0, 0.0))
                    x2, y2 = self.nodes_pos.get(to_node, (0.0, 0.0))
                    length = math.hypot(x2 - x1, y2 - y1)
                
                # TÍNH TOÁN CHI PHÍ (COST = LENGTH / SPEED = THỜI GIAN ĐI CỦA CẠNH)
                weight = length / speed if speed > 0 else float('inf')
                
                if from_node not in self.graph:
                    self.graph[from_node] = []
                    self.distance_cache[from_node] = {}
                    self.path_cache[from_node] = {}
                if to_node not in self.graph:
                    self.graph[to_node] = []
                    self.distance_cache[to_node] = {}
                    self.path_cache[to_node] = {}
                    
                self.graph[from_node].append((to_node, weight, edge_id))
        except Exception as e:
            print(f"Warning: Could not parse edge file {edge_file}: {e}")

    def get_shortest_path_cost(self, source: str, target: str) -> float:
        if source == target:
            return 0.0
        if source not in self.graph or target not in self.graph:
            return float('inf')
        if target in self.distance_cache.get(source, {}):
            return self.distance_cache[source][target]
        self._dijkstra(source, target)
        return self.distance_cache[source].get(target, float('inf'))

    def get_shortest_path_edges(self, source: str, target: str) -> List[str]:
        if source == target:
            return []
        if source not in self.graph or target not in self.graph:
            return []
        if target not in self.path_cache.get(source, {}):
            self._dijkstra(source, target)
        return self.path_cache[source].get(target, [])

    def _dijkstra(self, source: str, target: str) -> None:
        pq = [(0.0, source)]
        distances = {node: float('inf') for node in self.graph}
        distances[source] = 0.0
        
        pred: Dict[str, Tuple[str, str]] = {}
        
        while pq:
            current_dist, current_node = heapq.heappop(pq)
            
            if current_dist > distances[current_node]:
                continue
                
            if current_node == target:
                break
                
            for neighbor, weight, edge_id in self.graph[current_node]:
                distance = current_dist + weight
                if distance < distances[neighbor]:
                    distances[neighbor] = distance
                    pred[neighbor] = (current_node, edge_id)
                    heapq.heappush(pq, (distance, neighbor))
                    
        # Reconstruct path and cache the result
        if distances[target] != float('inf'):
            self.distance_cache[source][target] = distances[target]
            
            path_edges = []
            curr = target
            while curr != source:
                prev_node, e_id = pred[curr]
                path_edges.append(e_id)
                curr = prev_node
            path_edges.reverse()
            self.path_cache[source][target] = path_edges
