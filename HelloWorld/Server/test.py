from SUMO_xml import create_city_map, map_header, write_to_xml

if __name__ == "__main__":
    city_map_path = "./map/Boston_0_256.map"  # Đường dẫn tệp bản đồ thành phố

    
    # Tạo bản đồ thành phố và ghi các cạnh vào tệp XML
    create_city_map.create_map(city_map_path, numLanes=8, carSpeed=13.9, pedSpeed=1.4)
