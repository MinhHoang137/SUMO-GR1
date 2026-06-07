"""Loader kịch bản dựng-sẵn: copy .net.xml/.rou.xml (+ ghi .sumocfg chuẩn) từ một
thư mục vào SUMO_xml/ với tên chuẩn (HelloWorld.*) và bỏ qua sinh route tự động.

VAI TRÒ THỰC TẾ: hàm này được luồng OSM auto-gen TÁI SỬ DỤNG làm bước nạp lúc chạy.
launcher OSM tab gọi build_scenario (osm/) để sinh net+rou+cfg vào SUMO_xml/, rồi
truyền chính thư mục SUMO_xml/ cho main.py → main.py thấy isdir → config["custom"]=True
→ initialize_map_and_routes gọi apply_custom_script để chốt bộ file. KHÔNG xóa: luồng
OSM đang phụ thuộc hàm này.

KHÔNG tồn tại (tính năng tương lai): không có mode hướng-người-dùng "tự dựng kịch bản
trong netedit rồi trỏ server vào" — launcher chỉ có Benchmark / VRP / OSM. Tên gọi
"Custom Script" chỉ là cơ chế nội bộ, KHÔNG phải một mode người dùng chọn được."""

import os
import shutil
import xml.etree.ElementTree as ET

SUMO_XML_DIR = "SUMO_xml"
TARGET_NET = os.path.join(SUMO_XML_DIR, "HelloWorld.net.xml")
TARGET_ROU = os.path.join(SUMO_XML_DIR, "HelloWorld.rou.xml")
TARGET_CFG = os.path.join(SUMO_XML_DIR, "HelloWorld.sumocfg")


def _find_first(folder, ext):
    for name in sorted(os.listdir(folder)):
        if name.lower().endswith(ext):
            return os.path.join(folder, name)
    return None


def _copy_if_different(src, dst):
    """Copy src→dst trừ khi đã trỏ cùng inode (vd: OSM launcher đã ghi thẳng vào SUMO_xml/).
    shutil.copyfile sẽ raise SameFileError trong trường hợp đó."""
    try:
        if os.path.exists(dst) and os.path.samefile(src, dst):
            return
    except OSError:
        pass
    shutil.copyfile(src, dst)


def _read_cfg_inputs(sumocfg_path):
    """Đọc net-file và route-files (giá trị đầu tiên) khai báo trong .sumocfg."""
    try:
        tree = ET.parse(sumocfg_path)
        root = tree.getroot()
        net = root.find(".//net-file")
        rou = root.find(".//route-files")
        net_val = net.get("value") if net is not None else None
        rou_val = rou.get("value") if rou is not None else None
        # route-files có thể chứa nhiều file ngăn bằng dấu phẩy/space
        if rou_val:
            rou_val = rou_val.replace(",", " ").split()[0]
        return net_val, rou_val
    except Exception as e:
        print(f"[Warn] Không đọc được {sumocfg_path}: {e}")
        return None, None


def apply_custom_script(folder):
    """Sao chép kịch bản user-provided từ `folder` vào SUMO_xml/ với tên chuẩn.

    Yêu cầu folder chứa ít nhất .net.xml và .rou.xml; .sumocfg (nếu có) được dùng
    để xác định cặp net + route đúng khi folder chứa nhiều file. Hàm trả về
    True nếu thành công."""
    if not os.path.isdir(folder):
        print(f"[Error] Custom script folder không tồn tại: {folder}")
        return False

    cfg = _find_first(folder, ".sumocfg")
    net_path = None
    rou_path = None

    if cfg:
        net_name, rou_name = _read_cfg_inputs(cfg)
        if net_name:
            cand = os.path.join(folder, net_name)
            if os.path.isfile(cand):
                net_path = cand
        if rou_name:
            cand = os.path.join(folder, rou_name)
            if os.path.isfile(cand):
                rou_path = cand

    # Fallback: tự dò file đầu tiên đúng đuôi nếu sumocfg thiếu hoặc tham chiếu sai
    if not net_path:
        net_path = _find_first(folder, ".net.xml")
    if not rou_path:
        rou_path = _find_first(folder, ".rou.xml")

    if not net_path:
        print(f"[Error] Không tìm thấy file .net.xml trong {folder}")
        return False
    if not rou_path:
        print(f"[Error] Không tìm thấy file .rou.xml trong {folder}")
        return False

    os.makedirs(SUMO_XML_DIR, exist_ok=True)
    _copy_if_different(net_path, TARGET_NET)
    _copy_if_different(rou_path, TARGET_ROU)

    # Ghi đè sumocfg chuẩn để traci.start luôn dùng đúng cặp file vừa copy
    cfg_xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<sumoConfiguration xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
        'xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/sumoConfiguration.xsd">\n'
        '    <input>\n'
        '        <net-file value="HelloWorld.net.xml"/>\n'
        '        <route-files value="HelloWorld.rou.xml"/>\n'
        '    </input>\n'
        '</sumoConfiguration>\n'
    )
    with open(TARGET_CFG, "w", encoding="utf-8") as f:
        f.write(cfg_xml)

    print(f"[Info] Custom Script: copied net={os.path.basename(net_path)}, "
          f"rou={os.path.basename(rou_path)} vào {SUMO_XML_DIR}/")
    return True
