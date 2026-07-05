"""SUMO-Unity System Launcher — 3 tab simulation:
    Tab 1: chạy mô phỏng từ maze (.map).
    Tab 2: chạy mô phỏng từ OSM (.osm) — tự build .net.xml + .rou.xml + .sumocfg
           vào Server/SUMO_xml/ rồi launch ở chế độ Custom Script.
    Tab 3: chạy kịch bản do người dùng tự dựng bằng netedit — chỉ cần trỏ thư mục
           chứa .net.xml + .rou.xml (+ tuỳ chọn .sumocfg).

Phần shared (dưới notebook): Chế độ hiển thị, Theo dõi mô phỏng, Khởi động Server, Dừng tất cả —
dispatch theo tab đang active."""

import os
import sys
import shutil
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

# Ánh xạ trạng thái server sang tiếng Việt
_STATE_VI = {
    "PLAYING": "ĐANG CHẠY",
    "STOPPED": "ĐÃ DỪNG",
    "PAUSED": "TẠM DỪNG",
    "STARTING": "ĐANG KHỞI ĐỘNG",
}


class ScrollableFrame(ttk.Frame):
    """Frame có thanh cuộn dọc; nội dung đặt vào .inner."""
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self._canvas = tk.Canvas(self, highlightthickness=0)
        sb = ttk.Scrollbar(self, orient="vertical", command=self._canvas.yview)
        self.inner = ttk.Frame(self._canvas)
        self.inner.bind("<Configure>", lambda _e: self._canvas.configure(
            scrollregion=self._canvas.bbox("all")))
        self._win_id = self._canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self._canvas.configure(yscrollcommand=sb.set)
        self._canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self._canvas.bind("<Configure>", lambda e: self._canvas.itemconfig(
            self._win_id, width=e.width))
        self._canvas.bind("<Enter>", lambda _e: self._canvas.bind_all(
            "<MouseWheel>", lambda e: self._canvas.yview_scroll(-1*(e.delta//120), "units")))
        self._canvas.bind("<Leave>", lambda _e: self._canvas.unbind_all("<MouseWheel>"))


class ClampedSpinbox(ttk.Spinbox):
    """Spinbox tự snap về [from_, to] khi người dùng rời field (FocusOut)."""
    def __init__(self, parent, **kw):
        lo = kw.get('from_', 0)
        hi = kw.get('to', 100)
        var = kw.get('textvariable')
        super().__init__(parent, **kw)
        self._lo = lo
        self._hi = hi
        self._is_int = not (isinstance(lo, float) or isinstance(hi, float)
                            or isinstance(var, tk.DoubleVar))
        self.bind('<FocusOut>', self._clamp)

    def _clamp(self, _e=None):
        try:
            v = max(float(self._lo), min(float(self._hi), float(self.get())))
            self.set(int(round(v)) if self._is_int else v)
        except (ValueError, tk.TclError):
            self.set(self._lo)


class AppLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("SUMO-Unity: Khởi chạy hệ thống")
        self.root.geometry("640x820")
        self.root.resizable(True, True)

        # ── Shared paths ──────────────────────────────────────────────
        if getattr(sys, 'frozen', False):
            self.base_dir = os.path.dirname(sys.executable)
        else:
            self.base_dir = os.path.abspath(os.path.dirname(__file__))
        self.server_dir = os.path.join(self.base_dir, "Server")
        self.sumo_xml_dir = os.path.join(self.server_dir, "SUMO_xml")

        # ── Tab 1 (maze) vars ─────────────────────────────────────────
        self.map_file = tk.StringVar()
        self.num_lanes = tk.IntVar(value=2)
        self.sim_mode = tk.IntVar(value=1)  # 1: Benchmark, 2: VRP
        self.render_mode = tk.IntVar(value=1)  # 1: Realtime, 2: Pre-render
        self.num_pairs = tk.IntVar(value=20)
        self.car_cr_type = tk.StringVar(value="CS")
        self.has_ped = tk.BooleanVar(value=True)
        self.ped_cr_type = tk.StringVar(value="CS")
        self.ped_impatience = tk.DoubleVar(value=0.5)
        self.num_clients = tk.IntVar(value=10)
        self.num_staff = tk.IntVar(value=3)
        self.car_period = tk.DoubleVar(value=30.0)   # tần suất sinh xe (s)
        self.ped_period = tk.DoubleVar(value=30.0)   # tần suất sinh người đi bộ (s)
        self.sim_duration = tk.DoubleVar(value=3600.0)  # độ dài mô phỏng (s)
        self.enable_cap = tk.BooleanVar(value=False)
        self.max_vehicles = tk.IntVar(value=100)
        self.max_ped_count = tk.IntVar(value=100)

        # ── Tab 2 (OSM) vars ──────────────────────────────────────────
        self.osm_net_path = os.path.join(self.sumo_xml_dir, "HelloWorld.net.xml")
        self.osm_output_str = tk.StringVar(value="(chọn file .osm trước)")

        # ── Tab 3 (Custom Script) vars ────────────────────────────────
        self.custom_folder = tk.StringVar()
        self.osm_file = tk.StringVar()
        self.osm_mode = tk.StringVar(value="2d")
        self.osm_num_junctions = tk.StringVar(value="20")
        self.osm_edges_per_route = tk.StringVar(value="5")
        self.osm_algorithm = tk.StringVar(value="random")
        self.osm_gen_car = tk.BooleanVar(value=True)
        self.osm_gen_ped = tk.BooleanVar(value=True)
        self.osm_ped_impatience = tk.StringVar(value="0.5")
        self.osm_car_period = tk.StringVar(value="30")    # tần suất sinh xe (s)
        self.osm_ped_period = tk.StringVar(value="30")    # tần suất sinh người đi bộ (s)
        self.osm_sim_duration = tk.StringVar(value="3600")  # độ dài mô phỏng (s)

        # ── Shared vars ───────────────────────────────────────────────
        # Chế độ hiển thị realtime: 1 = chỉ 3D (Unity), 2 = cả 2D (sumo-gui) và 3D.
        self.gui_mode = tk.IntVar(value=1)
        self.server_process = None

        self._build_ui()
        self._toggle_mode()
        self._toggle_gui()
        self._toggle_cap()
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

    # ═════════════════════════════════════════════════════════════════
    # UI scaffolding
    # ═════════════════════════════════════════════════════════════════

    def _build_ui(self):
        root_frame = ttk.Frame(self.root, padding=10)
        root_frame.pack(fill=tk.BOTH, expand=True)

        self.notebook = ttk.Notebook(root_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        osm_tab = ttk.Frame(self.notebook)
        custom_tab = ttk.Frame(self.notebook)
        maze_tab = ttk.Frame(self.notebook)
        self.notebook.add(osm_tab, text="Mô phỏng OSM (.osm)")
        self.notebook.add(custom_tab, text="Kịch bản netedit")
        self.notebook.add(maze_tab, text="Mô phỏng Maze (.map)")

        self._build_osm_tab(osm_tab)
        self._build_custom_tab(custom_tab)
        self._build_maze_tab(maze_tab)
        self._build_shared_section(root_frame)

    # ═════════════════════════════════════════════════════════════════
    # Tab 1 — Maze .map
    # ═════════════════════════════════════════════════════════════════

    def _build_maze_tab(self, parent):
        sf = ScrollableFrame(parent)
        sf.pack(fill=tk.BOTH, expand=True)
        main_frame = ttk.Frame(sf.inner, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_frame, text="Kiểu bản đồ:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Label(main_frame, text="Maze (.map)").grid(row=0, column=1, sticky=tk.W, padx=5)

        ttk.Label(main_frame, text="Tệp bản đồ (.map):").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.map_file, width=40).grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(main_frame, text="Duyệt...", command=self._browse_map).grid(row=1, column=2, pady=5)

        ttk.Label(main_frame, text="Số làn (xe/bên):").grid(row=2, column=0, sticky=tk.W, pady=5)
        lane_frame = ttk.Frame(main_frame)
        lane_frame.grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
        ClampedSpinbox(lane_frame, from_=1, to=3, textvariable=self.num_lanes, width=10).pack(side=tk.LEFT)
        ttk.Label(lane_frame, text="(1–3 làn xe mỗi bên, +1 làn đi bộ)",
                  foreground="#666").pack(side=tk.LEFT, padx=6)

        ttk.Label(main_frame, text="Chế độ mô phỏng:").grid(row=3, column=0, sticky=tk.W, pady=5)
        mode_frame = ttk.Frame(main_frame)
        mode_frame.grid(row=3, column=1, sticky=tk.W)
        ttk.Radiobutton(mode_frame, text="1. Benchmark", variable=self.sim_mode,
                        value=1, command=self._toggle_mode).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(mode_frame, text="2. VRP", variable=self.sim_mode,
                        value=2, command=self._toggle_mode).pack(side=tk.LEFT, padx=5)

        ttk.Label(main_frame, text="Chế độ kết xuất:").grid(row=4, column=0, sticky=tk.W, pady=5)
        render_frame = ttk.Frame(main_frame)
        render_frame.grid(row=4, column=1, sticky=tk.W)
        ttk.Radiobutton(render_frame, text="Thời gian thực", variable=self.render_mode, value=1, command=self._toggle_gui).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(render_frame, text="Tiền kết xuất", variable=self.render_mode, value=2, command=self._toggle_gui).pack(side=tk.LEFT, padx=5)

        # Benchmark frame
        self.bench_frame = ttk.LabelFrame(main_frame, text="Tùy chọn Benchmark", padding=10)
        self.bench_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)

        ttk.Label(self.bench_frame, text="Số cặp nguồn–đích:").grid(row=0, column=0, sticky=tk.W, pady=2)
        ClampedSpinbox(self.bench_frame, from_=1, to=1000, textvariable=self.num_pairs, width=10).grid(row=0, column=1, sticky=tk.W, pady=2)

        ttk.Label(self.bench_frame, text="Kiểu nút giao (xe):").grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Combobox(self.bench_frame, textvariable=self.car_cr_type,
                     values=["CS", "SS", "IO", "OI"], width=8, state="readonly").grid(row=1, column=1, sticky=tk.W, pady=2)

        ttk.Label(self.bench_frame, text="Tần suất sinh xe (s):").grid(row=2, column=0, sticky=tk.W, pady=2)
        ClampedSpinbox(self.bench_frame, from_=1, to=600, increment=1,
                    textvariable=self.car_period, width=10).grid(row=2, column=1, sticky=tk.W, pady=2)

        ttk.Checkbutton(self.bench_frame, text="Tạo người đi bộ?",
                        variable=self.has_ped, command=self._toggle_ped).grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=5)

        self.ped_cr_lbl = ttk.Label(self.bench_frame, text="Kiểu nút giao (người đi bộ):")
        self.ped_cr_lbl.grid(row=4, column=0, sticky=tk.W, pady=2)
        self.ped_cr_cb = ttk.Combobox(self.bench_frame, textvariable=self.ped_cr_type,
                                       values=["CS", "SS", "IO", "OI"], width=8, state="readonly")
        self.ped_cr_cb.grid(row=4, column=1, sticky=tk.W, pady=2)

        self.ped_imp_lbl = ttk.Label(self.bench_frame, text="Độ thiếu kiên nhẫn người đi bộ (0–1):")
        self.ped_imp_lbl.grid(row=5, column=0, sticky=tk.W, pady=2)
        self.ped_imp_sb = ClampedSpinbox(self.bench_frame, from_=0.0, to=1.0,
                                       increment=0.1, textvariable=self.ped_impatience, width=10)
        self.ped_imp_sb.grid(row=5, column=1, sticky=tk.W, pady=2)

        self.ped_period_lbl = ttk.Label(self.bench_frame, text="Tần suất sinh người đi bộ (s):")
        self.ped_period_lbl.grid(row=6, column=0, sticky=tk.W, pady=2)
        self.ped_period_sb = ClampedSpinbox(self.bench_frame, from_=1, to=600, increment=1,
                                          textvariable=self.ped_period, width=10)
        self.ped_period_sb.grid(row=6, column=1, sticky=tk.W, pady=2)

        ttk.Label(self.bench_frame, text="Độ dài mô phỏng (s):").grid(row=7, column=0, sticky=tk.W, pady=2)
        ClampedSpinbox(self.bench_frame, from_=60, to=86400, increment=60,
                    textvariable=self.sim_duration, width=10).grid(row=7, column=1, sticky=tk.W, pady=2)

        ttk.Checkbutton(self.bench_frame, text="Giới hạn đối tượng gửi xuống Unity?",
                        variable=self.enable_cap, command=self._toggle_cap).grid(row=8, column=0, columnspan=2, sticky=tk.W, pady=5)

        self.max_v_lbl = ttk.Label(self.bench_frame, text="Số xe tối đa:")
        self.max_v_lbl.grid(row=9, column=0, sticky=tk.W, pady=2)
        self.max_v_sb = ClampedSpinbox(self.bench_frame, from_=1, to=10000, textvariable=self.max_vehicles, width=10)
        self.max_v_sb.grid(row=9, column=1, sticky=tk.W, pady=2)

        self.max_p_lbl = ttk.Label(self.bench_frame, text="Số người đi bộ tối đa:")
        self.max_p_lbl.grid(row=10, column=0, sticky=tk.W, pady=2)
        self.max_p_sb = ClampedSpinbox(self.bench_frame, from_=1, to=10000, textvariable=self.max_ped_count, width=10)
        self.max_p_sb.grid(row=10, column=1, sticky=tk.W, pady=2)

        # VRP frame
        self.vrp_frame = ttk.LabelFrame(main_frame, text="Tùy chọn VRP", padding=10)
        self.vrp_frame.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)

        ttk.Label(self.vrp_frame, text="Số khách hàng:").grid(row=0, column=0, sticky=tk.W, pady=2)
        ClampedSpinbox(self.vrp_frame, from_=1, to=1000, textvariable=self.num_clients, width=10).grid(row=0, column=1, sticky=tk.W, pady=2)

        ttk.Label(self.vrp_frame, text="Số nhân viên:").grid(row=1, column=0, sticky=tk.W, pady=2)
        ClampedSpinbox(self.vrp_frame, from_=1, to=100, textvariable=self.num_staff, width=10).grid(row=1, column=1, sticky=tk.W, pady=2)

    def _browse_map(self):
        init_dir = os.path.join(self.server_dir, "map")
        if not os.path.exists(init_dir):
            init_dir = self.base_dir
        path = filedialog.askopenfilename(
            initialdir=init_dir, title="Chọn tệp bản đồ",
            filetypes=[("Tệp bản đồ", "*.map"), ("Tất cả tệp", "*.*")],
        )
        if path:
            self.map_file.set(path)

    def _toggle_mode(self):
        if self.sim_mode.get() == 1:
            for child in self.bench_frame.winfo_children(): child.configure(state='normal')
            for child in self.vrp_frame.winfo_children(): child.configure(state='disabled')
            self._toggle_ped()
            self._toggle_cap()
        else:
            for child in self.bench_frame.winfo_children(): child.configure(state='disabled')
            for child in self.vrp_frame.winfo_children(): child.configure(state='normal')

    def _toggle_gui(self):
        # Chế độ hiển thị chỉ áp dụng cho realtime; pre-render luôn headless.
        state = 'normal' if self.render_mode.get() == 1 else 'disabled'
        if hasattr(self, 'gui_3d_rb'):
            self.gui_3d_rb.configure(state=state)
            self.gui_2d3d_rb.configure(state=state)

    def _toggle_ped(self):
        if self.has_ped.get():
            self.ped_cr_lbl.configure(state='normal')
            self.ped_cr_cb.configure(state='readonly')
            self.ped_imp_lbl.configure(state='normal')
            self.ped_imp_sb.configure(state='normal')
            self.ped_period_lbl.configure(state='normal')
            self.ped_period_sb.configure(state='normal')
        else:
            self.ped_cr_lbl.configure(state='disabled')
            self.ped_cr_cb.configure(state='disabled')
            self.ped_imp_lbl.configure(state='disabled')
            self.ped_imp_sb.configure(state='disabled')
            self.ped_period_lbl.configure(state='disabled')
            self.ped_period_sb.configure(state='disabled')

    def _toggle_cap(self):
        if not hasattr(self, 'max_v_lbl'):
            return
        state = 'normal' if self.enable_cap.get() else 'disabled'
        for w in [self.max_v_lbl, self.max_v_sb, self.max_p_lbl, self.max_p_sb]:
            w.configure(state=state)
        if hasattr(self, 'osm_max_v_lbl'):
            for w in [self.osm_max_v_lbl, self.osm_max_v_sb, self.osm_max_p_lbl, self.osm_max_p_sb]:
                w.configure(state=state)

    # ═════════════════════════════════════════════════════════════════
    # Tab 2 — OSM .osm
    # ═════════════════════════════════════════════════════════════════

    def _build_osm_tab(self, parent):
        sf = ScrollableFrame(parent)
        sf.pack(fill=tk.BOTH, expand=True)
        frame = ttk.Frame(sf.inner, padding=15)
        frame.pack(fill=tk.BOTH, expand=True)
        frame.columnconfigure(1, weight=1)

        ttk.Label(frame, text="Tệp OSM (.osm):").grid(row=0, column=0, sticky=tk.W, pady=4)
        ttk.Entry(frame, textvariable=self.osm_file).grid(row=0, column=1, columnspan=3, sticky=tk.EW, padx=5, pady=4)
        ttk.Button(frame, text="Duyệt...", command=self._browse_osm).grid(row=0, column=4, pady=4)

        ttk.Label(frame, text="→ Đầu ra:", foreground="#555").grid(row=1, column=0, sticky=tk.W, pady=4)
        ttk.Label(frame, textvariable=self.osm_output_str,
                  foreground="#555").grid(row=1, column=1, columnspan=4, sticky=tk.W, padx=5)

        ttk.Separator(frame, orient=tk.HORIZONTAL).grid(row=2, column=0, columnspan=5, sticky=tk.EW, pady=8)

        ttk.Label(frame, text="Chế độ bản đồ:").grid(row=3, column=0, sticky=tk.W, pady=4)
        mode_frame = ttk.Frame(frame)
        mode_frame.grid(row=3, column=1, columnspan=4, sticky=tk.W)
        ttk.Radiobutton(mode_frame, text="2D (khuyến khích — bản đồ không có cầu vượt chồng chéo)",
                        variable=self.osm_mode, value="2d").pack(anchor=tk.W)
        ttk.Radiobutton(mode_frame, text="3D (giữ cao độ + cầu vượt — khi cần chính xác)",
                        variable=self.osm_mode, value="3d").pack(anchor=tk.W)

        ttk.Label(frame, text="Số junction:").grid(row=4, column=0, sticky=tk.W, pady=4)
        ClampedSpinbox(frame, textvariable=self.osm_num_junctions, from_=0, to=9999, width=8).grid(row=4, column=1, sticky=tk.W, padx=5, pady=4)
        ttk.Label(frame, text="(lấy tối đa nếu vượt số khả dụng)",
                  foreground="#666").grid(row=4, column=2, columnspan=3, sticky=tk.W)

        ttk.Label(frame, text="Độ dài tuyến:").grid(row=5, column=0, sticky=tk.W, pady=4)
        ClampedSpinbox(frame, textvariable=self.osm_edges_per_route, from_=1, to=30, width=8).grid(row=5, column=1, sticky=tk.W, padx=5, pady=4)
        ttk.Label(frame, text="(số đoạn đường liên tiếp mỗi xe/người đi qua)",
                  foreground="#666").grid(row=5, column=2, columnspan=3, sticky=tk.W)

        ttk.Label(frame, text="Thuật toán:").grid(row=6, column=0, sticky=tk.W, pady=4)
        algo_frame = ttk.Frame(frame)
        algo_frame.grid(row=6, column=1, columnspan=4, sticky=tk.W)
        ttk.Radiobutton(algo_frame, text="Random (độ dài ngẫu nhiên 1..K, có thể dừng sớm)",
                        variable=self.osm_algorithm, value="random").pack(anchor=tk.W)
        ttk.Radiobutton(algo_frame, text="Maximum (cố gắng đủ K đoạn, có thể dừng sớm)",
                        variable=self.osm_algorithm, value="max").pack(anchor=tk.W)

        ttk.Label(frame, text="Sinh tuyến cho:").grid(row=7, column=0, sticky=tk.W, pady=4)
        types_frame = ttk.Frame(frame)
        types_frame.grid(row=7, column=1, columnspan=4, sticky=tk.W)
        ttk.Checkbutton(types_frame, text="Xe", variable=self.osm_gen_car).pack(side=tk.LEFT, padx=(0, 12))
        ttk.Checkbutton(types_frame, text="Người đi bộ", variable=self.osm_gen_ped).pack(side=tk.LEFT, padx=(0, 12))
        ttk.Label(types_frame, text="Độ thiếu kiên nhẫn:").pack(side=tk.LEFT)
        ClampedSpinbox(types_frame, textvariable=self.osm_ped_impatience, from_=0.0, to=1.0, increment=0.1, width=6).pack(side=tk.LEFT, padx=4)

        ttk.Label(frame, text="Tần suất sinh (s):").grid(row=8, column=0, sticky=tk.W, pady=4)
        period_frame = ttk.Frame(frame)
        period_frame.grid(row=8, column=1, columnspan=4, sticky=tk.W)
        ttk.Label(period_frame, text="Xe:").pack(side=tk.LEFT)
        ClampedSpinbox(period_frame, textvariable=self.osm_car_period, from_=0, to=3600, width=6).pack(side=tk.LEFT, padx=(2, 12))
        ttk.Label(period_frame, text="Người đi bộ:").pack(side=tk.LEFT)
        ClampedSpinbox(period_frame, textvariable=self.osm_ped_period, from_=0, to=3600, width=6).pack(side=tk.LEFT, padx=2)

        ttk.Label(frame, text="Độ dài mô phỏng (s):").grid(row=9, column=0, sticky=tk.W, pady=4)
        ClampedSpinbox(frame, textvariable=self.osm_sim_duration, from_=0, to=86400, increment=60, width=8).grid(row=9, column=1, sticky=tk.W, padx=5, pady=4)
        ttk.Label(frame, text="(thời điểm dừng sinh xe/người)",
                  foreground="#666").grid(row=9, column=2, columnspan=3, sticky=tk.W)

        # Render Mode — share self.render_mode với Tab Maze để 2 tab đồng bộ
        ttk.Label(frame, text="Chế độ kết xuất:").grid(row=10, column=0, sticky=tk.W, pady=4)
        render_frame = ttk.Frame(frame)
        render_frame.grid(row=10, column=1, columnspan=4, sticky=tk.W)
        ttk.Radiobutton(render_frame, text="Thời gian thực", variable=self.render_mode, value=1, command=self._toggle_gui).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(render_frame, text="Tiền kết xuất", variable=self.render_mode, value=2, command=self._toggle_gui).pack(side=tk.LEFT, padx=5)

        ttk.Separator(frame, orient=tk.HORIZONTAL).grid(row=11, column=0, columnspan=5, sticky=tk.EW, pady=8)

        ttk.Checkbutton(frame, text="Giới hạn đối tượng gửi xuống Unity?",
                        variable=self.enable_cap, command=self._toggle_cap).grid(row=12, column=0, columnspan=2, sticky=tk.W, pady=4)

        self.osm_max_v_lbl = ttk.Label(frame, text="Số xe tối đa:")
        self.osm_max_v_lbl.grid(row=13, column=0, sticky=tk.W, pady=2)
        self.osm_max_v_sb = ClampedSpinbox(frame, from_=1, to=10000, textvariable=self.max_vehicles, width=10)
        self.osm_max_v_sb.grid(row=13, column=1, sticky=tk.W, padx=5, pady=2)

        self.osm_max_p_lbl = ttk.Label(frame, text="Số người đi bộ tối đa:")
        self.osm_max_p_lbl.grid(row=14, column=0, sticky=tk.W, pady=2)
        self.osm_max_p_sb = ClampedSpinbox(frame, from_=1, to=10000, textvariable=self.max_ped_count, width=10)
        self.osm_max_p_sb.grid(row=14, column=1, sticky=tk.W, padx=5, pady=2)

    def _get_osm_result_dir(self):
        osm = self.osm_file.get()
        name = os.path.splitext(os.path.basename(osm))[0] if osm else "output"
        return os.path.join(self.server_dir, "result", name)

    def _browse_osm(self):
        init_dir = os.path.join(self.server_dir, "osm")
        if not os.path.isdir(init_dir):
            init_dir = self.base_dir
        path = filedialog.askopenfilename(
            initialdir=init_dir, title="Chọn tệp OSM",
            filetypes=[("Tệp OSM", "*.osm"), ("Tất cả tệp", "*.*")],
        )
        if path:
            self.osm_file.set(path)
            rel = os.path.relpath(self._get_osm_result_dir(), self.base_dir)
            self.osm_output_str.set(f"{rel}/HelloWorld.net.xml (+ .rou.xml + .sumocfg)")

    # ═════════════════════════════════════════════════════════════════
    # Tab 3 — Custom Script (netedit)
    # ═════════════════════════════════════════════════════════════════

    def _build_custom_tab(self, parent):
        frame = ttk.Frame(parent, padding=15)
        frame.pack(fill=tk.BOTH, expand=True)
        frame.columnconfigure(1, weight=1)

        # Hướng dẫn
        info = ttk.LabelFrame(frame, text="Hướng dẫn", padding=10)
        info.grid(row=0, column=0, columnspan=3, sticky=tk.EW, pady=(0, 10))
        ttk.Label(info, text=(
            "1. Dùng netedit để tạo mạng lưới đường (network) và tuyến đường (routes).\n"
            "2. Export ra .net.xml và .rou.xml vào cùng 1 thư mục.\n"
            "3. Chọn thư mục đó bên dưới rồi nhấn Khởi động Server."
        ), justify=tk.LEFT, foreground="#333").pack(anchor=tk.W)

        ttk.Separator(frame, orient=tk.HORIZONTAL).grid(row=1, column=0, columnspan=3, sticky=tk.EW, pady=8)

        ttk.Label(frame, text="Thư mục kịch bản:").grid(row=2, column=0, sticky=tk.W, pady=4)
        ttk.Entry(frame, textvariable=self.custom_folder).grid(row=2, column=1, sticky=tk.EW, padx=5, pady=4)
        ttk.Button(frame, text="Duyệt...", command=self._browse_custom_folder).grid(row=2, column=2, pady=4)

        ttk.Label(frame, text="→ Bắt buộc:", foreground="#555").grid(row=3, column=0, sticky=tk.W, pady=2)
        ttk.Label(frame, text=".net.xml  và  .rou.xml  (+ tuỳ chọn: .sumocfg)",
                  foreground="#555").grid(row=3, column=1, columnspan=2, sticky=tk.W, padx=5)

        ttk.Separator(frame, orient=tk.HORIZONTAL).grid(row=4, column=0, columnspan=3, sticky=tk.EW, pady=8)

        # Render Mode — chia sẻ cùng self.render_mode với 2 tab kia
        ttk.Label(frame, text="Chế độ kết xuất:").grid(row=5, column=0, sticky=tk.W, pady=4)
        render_frame = ttk.Frame(frame)
        render_frame.grid(row=5, column=1, columnspan=2, sticky=tk.W)
        ttk.Radiobutton(render_frame, text="Thời gian thực", variable=self.render_mode,
                        value=1, command=self._toggle_gui).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(render_frame, text="Tiền kết xuất", variable=self.render_mode,
                        value=2, command=self._toggle_gui).pack(side=tk.LEFT, padx=5)

    def _browse_custom_folder(self):
        path = filedialog.askdirectory(
            initialdir=self.base_dir,
            title="Chọn thư mục chứa kịch bản netedit (.net.xml + .rou.xml)",
        )
        if path:
            self.custom_folder.set(path)

    # ═════════════════════════════════════════════════════════════════
    # Shared section (dưới notebook)
    # ═════════════════════════════════════════════════════════════════

    def _build_shared_section(self, parent):
        shared = ttk.Frame(parent, padding=(15, 10, 15, 5))
        shared.pack(fill=tk.X)

        gui_frame = ttk.Frame(shared)
        gui_frame.pack(anchor=tk.W, pady=(0, 5))
        ttk.Label(gui_frame, text="Chế độ hiển thị (Thời gian thực):").pack(side=tk.LEFT, padx=(0, 8))
        self.gui_3d_rb = ttk.Radiobutton(gui_frame, text="Chỉ 3D", variable=self.gui_mode, value=1)
        self.gui_3d_rb.pack(side=tk.LEFT, padx=4)
        self.gui_2d3d_rb = ttk.Radiobutton(gui_frame, text="Cả 2D và 3D", variable=self.gui_mode, value=2)
        self.gui_2d3d_rb.pack(side=tk.LEFT, padx=4)

        monitor = ttk.LabelFrame(shared, text="Theo dõi mô phỏng", padding=10)
        monitor.pack(fill=tk.X, pady=5)
        self.status_lbl = ttk.Label(monitor, text="Trạng thái: CHƯA CHẠY",
                                    font=("Segoe UI", 10, "bold"), foreground="blue")
        self.status_lbl.grid(row=0, column=0, sticky=tk.W, pady=2)
        self.timestep_lbl = ttk.Label(monitor, text="Bước thời gian: N/A", font=("Segoe UI", 10))
        self.timestep_lbl.grid(row=1, column=0, sticky=tk.W, pady=2)

        btn_frame = tk.Frame(shared)
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text="Khởi động Server", font=("Segoe UI", 11, "bold"),
                  bg="#4CAF50", fg="white", width=15, command=self._start_server).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="Dừng tất cả", font=("Segoe UI", 11, "bold"),
                  bg="#f44336", fg="white", width=15, command=self._stop_all).pack(side=tk.LEFT, padx=10)

    # ═════════════════════════════════════════════════════════════════
    # Start Server — dispatch theo tab
    # ═════════════════════════════════════════════════════════════════

    def _start_server(self):
        if self.server_process and self.server_process.poll() is None:
            messagebox.showinfo("Thông tin", "Server đang chạy rồi!")
            return

        active = self.notebook.index(self.notebook.select())
        if active == 0:
            self._start_from_osm()
        elif active == 1:
            self._start_from_custom()
        else:
            self._start_from_maze()

    # ── Tab 1 path: maze .map ────────────────────────────────────────
    def _start_from_maze(self):
        if not self.map_file.get():
            messagebox.showerror("Lỗi", "Hãy chọn 1 file .map.")
            return
        if not os.path.isfile(self.map_file.get()):
            messagebox.showerror("Lỗi", "File .map không tồn tại.")
            return

        inputs = [str(self.sim_mode.get())]
        if self.sim_mode.get() == 1:
            inputs.append(str(self.num_pairs.get()))
            inputs.append(self.car_cr_type.get())
            inputs.append(str(self.car_period.get()))
            inputs.append("y" if self.has_ped.get() else "n")
            if self.has_ped.get():
                inputs.append(self.ped_cr_type.get())
                inputs.append(str(self.ped_impatience.get()))
                inputs.append(str(self.ped_period.get()))
            inputs.append(str(self.sim_duration.get()))
            inputs.append("y" if self.enable_cap.get() else "n")
            if self.enable_cap.get():
                inputs.append(str(self.max_vehicles.get()))
                inputs.append(str(self.max_ped_count.get()))
        else:
            inputs.append(str(self.num_clients.get()))
            inputs.append(str(self.num_staff.get()))
        inputs.append(str(self.render_mode.get()))
        if self.render_mode.get() == 1:  # realtime mới cần chọn chế độ hiển thị
            inputs.append(str(self.gui_mode.get()))

        self._launch_main(self.map_file.get(), self.num_lanes.get(), inputs)

    # ── Tab 2 path: OSM → build scenario rồi launch custom script ───
    def _start_from_osm(self):
        osm = self.osm_file.get()
        if not osm or not os.path.isfile(osm):
            messagebox.showerror("Lỗi", "Hãy chọn 1 file .osm hợp lệ.")
            return
        if not (self.osm_gen_car.get() or self.osm_gen_ped.get()):
            messagebox.showerror("Lỗi", "Phải chọn ít nhất 1 trong 'Xe' hoặc 'Người đi bộ'.")
            return
        try:
            n_junc = int(self.osm_num_junctions.get())
            k_edges = int(self.osm_edges_per_route.get())
            ped_imp = float(self.osm_ped_impatience.get())
            car_period = float(self.osm_car_period.get())
            ped_period = float(self.osm_ped_period.get())
            end_time = float(self.osm_sim_duration.get())
        except ValueError:
            messagebox.showerror("Lỗi", "Số junction / edges / impatience / tần suất / độ dài phải là số hợp lệ.")
            return
        if n_junc <= 0 or k_edges <= 0:
            messagebox.showerror("Lỗi", "Số junction và edges/route phải > 0.")
            return
        if car_period <= 0 or ped_period <= 0 or end_time <= 0:
            messagebox.showerror("Lỗi", "Tần suất sinh và độ dài mô phỏng phải > 0.")
            return

        os.makedirs(self.sumo_xml_dir, exist_ok=True)
        params = {
            "osm": osm, "out": self.osm_net_path, "mode": self.osm_mode.get(),
            "num_junctions": n_junc, "edges_per_route": k_edges,
            "algorithm": self.osm_algorithm.get(),
            "gen_car": self.osm_gen_car.get(), "gen_ped": self.osm_gen_ped.get(),
            "ped_impatience": ped_imp,
            "car_period": car_period, "ped_period": ped_period, "end_time": end_time,
        }
        self.status_lbl.configure(text=f"Trạng thái: ĐANG XÂY DỰNG OSM ({params['mode'].upper()})…",
                                  foreground="orange")
        threading.Thread(target=self._build_then_launch, args=(params,), daemon=True).start()

    def _build_then_launch(self, params):
        if self.server_dir not in sys.path:
            sys.path.insert(0, self.server_dir)
        ok = False
        try:
            from osm.scenario import build_scenario
            ok = build_scenario(
                params["osm"], params["out"],
                mode=params["mode"],
                num_junctions=params["num_junctions"],
                edges_per_route=params["edges_per_route"],
                algorithm=params["algorithm"],
                gen_car=params["gen_car"],
                gen_ped=params["gen_ped"],
                ped_impatience=params["ped_impatience"],
                car_period=params["car_period"],
                ped_period=params["ped_period"],
                end_time=params["end_time"],
            )
        except Exception as e:
            print(f"[Error] {e}")
            import traceback; traceback.print_exc()
            ok = False

        def after_build():
            if not ok:
                self.status_lbl.configure(text="Trạng thái: XÂY DỰNG THẤT BẠI", foreground="red")
                messagebox.showerror(
                    "Thất bại",
                    "Xây dựng kịch bản OSM thất bại. Kiểm tra console (cần SUMO/netconvert trong PATH).",
                )
                return
            # Custom Script mode: pass folder path, main.py detect isdir
            inputs = [params["osm"]]  # session_name = path file .osm gốc
            inputs.append("y" if self.osm_gen_ped.get() else "n")
            inputs.append(str(self.render_mode.get()))
            if self.render_mode.get() == 1:
                inputs.append(str(self.gui_mode.get()))
            inputs.append("y" if self.enable_cap.get() else "n")
            if self.enable_cap.get():
                inputs.append(str(self.max_vehicles.get()))
                inputs.append(str(self.max_ped_count.get()))
            self._launch_main(self.sumo_xml_dir, self.num_lanes.get(), inputs)

        self.root.after(0, after_build)

    # ── Tab 3 path: Custom Script (netedit) ─────────────────────────
    def _start_from_custom(self):
        folder = self.custom_folder.get().strip()
        if not folder:
            messagebox.showerror("Lỗi", "Hãy chọn thư mục chứa kịch bản netedit.")
            return
        if not os.path.isdir(folder):
            messagebox.showerror("Lỗi", "Thư mục không tồn tại.")
            return

        # Kiểm tra sơ bộ sự tồn tại file bắt buộc trước khi launch
        has_net = any(f.lower().endswith(".net.xml") for f in os.listdir(folder))
        has_rou = any(f.lower().endswith(".rou.xml") for f in os.listdir(folder))
        if not has_net or not has_rou:
            missing = []
            if not has_net:
                missing.append(".net.xml")
            if not has_rou:
                missing.append(".rou.xml")
            messagebox.showerror(
                "Lỗi",
                f"Thư mục thiếu file bắt buộc: {', '.join(missing)}\n"
                "Hãy export kịch bản từ netedit vào thư mục đã chọn.",
            )
            return

        inputs = [""]  # session_name trống → dùng tên thư mục
        inputs.append("n")  # tab netedit không có tuỳ chọn người đi bộ
        inputs.append(str(self.render_mode.get()))
        if self.render_mode.get() == 1:
            inputs.append(str(self.gui_mode.get()))
        inputs.append("n")  # không giới hạn đối tượng (custom tab không có UI cap)
        self._launch_main(folder, 1, inputs)

    # ── Subprocess + monitor (chung cho cả 3 tab) ────────────────────
    def _launch_main(self, map_path, num_lanes, inputs):
        try:
            python_cmd = "python" if getattr(sys, 'frozen', False) else sys.executable
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"
            cmd = [python_cmd, "main.py"]
            self.server_process = subprocess.Popen(
                cmd, cwd=self.server_dir,
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1, encoding='utf-8', errors='replace', env=env,
            )
            all_inputs = [map_path, str(num_lanes)] + inputs
            self.server_process.stdin.write("\n".join(all_inputs) + "\n")
            self.server_process.stdin.flush()
            self.status_lbl.configure(text="Trạng thái: ĐANG KHỞI ĐỘNG SERVER...", foreground="orange")
            threading.Thread(target=self._monitor_process, daemon=True).start()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể khởi động Server:\n{e}")

    def _monitor_process(self):
        if not self.server_process:
            return
        try:
            for line in iter(self.server_process.stdout.readline, ''):
                line = line.strip()
                if not line:
                    continue
                print(f"[Server] {line}")
                if "[MONITOR] STATE:" in line:
                    state = line.split("STATE:")[1].strip()
                    state_vi = _STATE_VI.get(state, state)
                    color = "green" if state == "PLAYING" else ("red" if state == "STOPPED" else "orange")
                    self.root.after(0, lambda s=state_vi, c=color: self.status_lbl.configure(text=f"Trạng thái: {s}", foreground=c))
                elif "[MONITOR] TIME_STEP:" in line:
                    ts = line.split("TIME_STEP:")[1].strip()
                    self.root.after(0, lambda t=ts: self.timestep_lbl.configure(text=f"Bước thời gian: {t}s"))
                elif "[MONITOR] CLIENT_CONNECTED" in line:
                    self.root.after(0, lambda: self.status_lbl.configure(text="Trạng thái: ĐÃ KẾT NỐI, ĐANG CHỜ...", foreground="blue"))
        except Exception as e:
            print(f"Monitor thread error: {e}")
        self.root.after(0, lambda: self.status_lbl.configure(text="Trạng thái: ĐÃ DỪNG", foreground="red"))
        self.root.after(0, lambda: self.timestep_lbl.configure(text="Bước thời gian: N/A"))

    def _stop_all(self):
        if self.server_process and self.server_process.poll() is None:
            self.server_process.terminate()
            self.server_process = None
            messagebox.showinfo("Thông tin", "Đã dừng các tiến trình đang chạy.")
        else:
            messagebox.showinfo("Thông tin", "Không có tiến trình nào đang chạy từ Launcher.")

    # ═════════════════════════════════════════════════════════════════
    # Shutdown
    # ═════════════════════════════════════════════════════════════════

    def _on_closing(self):
        if self.server_process and self.server_process.poll() is None:
            self.server_process.terminate()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    AppLauncher(root)
    root.mainloop()
