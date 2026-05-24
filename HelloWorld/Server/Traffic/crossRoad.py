

import os
import xml.etree.ElementTree as ET

class CrossRoadReader:
    NET_XML_PATH  = os.path.join(os.path.dirname(__file__), '../SUMO_xml/HelloWorld.net.xml')
    # Cache module-level cho get_junction_polygons — edgeType0 gọi mỗi lần snap, không parse XML lặp.
    _POLY_CACHE: "dict[str, list[tuple[float, float, float]]] | None" = None

    @classmethod
    def parse_shape(cls, shape):
        points = shape.strip().split(' ')
        vertices = []
        for p in points:
            coords = p.split(',')
            x = float(coords[0])
            y = float(coords[1])
            z = float(coords[2]) if len(coords) > 2 else 0.0
            vertices.append((x, y, z))
        return vertices

    @classmethod
    def get_junction_polygons(cls):
        """Trả về {junction_id: [(x, y, z), ...]} cho mọi junction có shape.

        Dùng cho snap lane endpoint vào polygon junction (edgeType0). Giữ thứ tự đỉnh gốc
        từ SUMO (đi vòng biên polygon). Cache module-level — gọi nhiều lần không re-parse.
        """
        if cls._POLY_CACHE is not None:
            return cls._POLY_CACHE
        cache: "dict[str, list[tuple[float, float, float]]]" = {}
        if not os.path.exists(cls.NET_XML_PATH):
            cls._POLY_CACHE = cache
            return cache
        try:
            root = ET.parse(cls.NET_XML_PATH).getroot()
        except ET.ParseError:
            cls._POLY_CACHE = cache
            return cache
        for junction in root.findall('junction'):
            jid = junction.get('id')
            shape = junction.get('shape')
            if not jid or not shape:
                continue
            verts = cls.parse_shape(shape)
            if len(verts) >= 3:
                cache[jid] = verts
        cls._POLY_CACHE = cache
        return cache

    @classmethod
    def read_all_junctions(cls):
        if not os.path.exists(cls.NET_XML_PATH):
            print(f"Error: {cls.NET_XML_PATH} does not exist.")
            return

        tree = ET.parse(cls.NET_XML_PATH)
        root = tree.getroot()

        crossroads = []

        for junction in root.findall('junction'):
            junction_id = junction.get('id')
            # junction_type = junction.get('type', 'unknown')
            x = float(junction.get('x'))
            y = float(junction.get('y'))
            z = float(junction.get('z', 0.0))
            shape = junction.get('shape')

            if shape:
                # Giữ nguyên thứ tự đỉnh do SUMO emit (đi vòng theo biên polygon — đúng cho concave).
                # KHÔNG re-sort theo góc quanh centroid: cách đó chỉ đúng với convex polygon và sẽ
                # tạo polygon tự cắt cho junction concave (ngã ba/tư có bo góc nhiều cạnh).
                vertices = cls.parse_shape(shape)
                crossroad = {
                    "i": junction_id,
                    "p": [round(x, 3), round(y, 3), round(z, 3)],
                    "v": [{"x": round(v[0], 3), "y": round(v[1], 3), "z": round(v[2], 3)} for v in vertices]
                }
                crossroads.append(crossroad)

        if not crossroads:
            print("No junctions found in the file.")

        return crossroads

if __name__ == "__main__":
    CrossRoadReader.read_all_junctions()
