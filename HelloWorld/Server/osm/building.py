

import os
import json


class BuildingReader:
    """Đọc polygon toà nhà đã trích sẵn từ .osm (chỉ tồn tại ở chế độ render OSM).

    Toà nhà KHÔNG thuộc về giao thông và không phải mode nào cũng có (benchmark /
    custom-script không sinh), nên reader nằm trong package osm/ thay vì Traffic/.

    File HelloWorld.buildings.json là cache TRUNG GIAN do osm.building_extractor ghi
    trong lúc build_scenario (lúc đó mới có .osm + sumolib để project). Runtime gộp nó
    vào dict road_data (khoá "bd") → road_data.json đầy đủ. Sau khi đã gộp+gửi xong,
    gọi discard() để xoá cache (xem send_road_data / run_prerender).
    """
    BUILDINGS_JSON_PATH = os.path.join(os.path.dirname(__file__), '../SUMO_xml/HelloWorld.buildings.json')
    NET_XML_PATH = os.path.join(os.path.dirname(__file__), '../SUMO_xml/HelloWorld.net.xml')

    @classmethod
    def read_buildings(cls):
        """Trả list building dict (schema {i,h,v}) hoặc [] nếu không có / đã cũ.

        Chống lệch map: nếu net.xml được dựng lại SAU buildings.json (vd chuyển sang
        benchmark hay map OSM khác), building cũ không còn khớp → bỏ qua.
        """
        path = cls.BUILDINGS_JSON_PATH
        if not os.path.exists(path):
            return []
        try:
            if (os.path.exists(cls.NET_XML_PATH)
                    and os.path.getmtime(path) < os.path.getmtime(cls.NET_XML_PATH)):
                return []  # stale: net mới hơn buildings → khác map
        except OSError:
            pass
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, list) else []
        except (OSError, ValueError) as e:
            print(f"[Building] Lỗi đọc {path}: {e}")
            return []

    @classmethod
    def discard(cls):
        """Xoá cache trung gian sau khi road_data.json đầy đủ đã được tạo/gửi."""
        try:
            if os.path.exists(cls.BUILDINGS_JSON_PATH):
                os.remove(cls.BUILDINGS_JSON_PATH)
                print(f"[Building] Đã xoá cache trung gian {cls.BUILDINGS_JSON_PATH}")
        except OSError as e:
            print(f"[Building] Không xoá được cache: {e}")


if __name__ == "__main__":
    print(f"{len(BuildingReader.read_buildings())} toà nhà trong {BuildingReader.BUILDINGS_JSON_PATH}")
