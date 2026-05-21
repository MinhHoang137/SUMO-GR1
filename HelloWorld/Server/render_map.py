import os
import sys
import json
from datetime import datetime

# Adds the Server directory to sys.path so modules can be imported correctly
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from Traffic.crossRoad import CrossRoadReader
from Traffic.edgeType0 import EdgeReader
from Traffic.crossing import CrossingReader

def render_map_from_net_xml():
    # Folder to save the map_json
    map_json_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "map_json")
    os.makedirs(map_json_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    road_data_file_path = os.path.join(map_json_dir, f"RoadData-{timestamp}.json")
    
    print("Reading data from .net.xml...")
    
    try:
        crossroads = CrossRoadReader.read_all_junctions()
        edges = EdgeReader.read_edges()
        crossings = CrossingReader.read_crossings()
        
        road_data = {
            "jd": crossroads,
            "ed": edges,
            "cd": crossings
        }
        
        with open(road_data_file_path, "w", encoding="utf-8") as rdf:
            json.dump(road_data, rdf, ensure_ascii=False, indent=4)
            
        print(f"Road data successfully saved to: {road_data_file_path}")
        
    except Exception as e:
        print(f"Error rendering map data: {e}")

if __name__ == "__main__":
    render_map_from_net_xml()
