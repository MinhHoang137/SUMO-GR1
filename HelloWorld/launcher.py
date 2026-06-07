"""SUMO-Unity System Launcher — 2 tab simulation:
    Tab 1: chạy mô phỏng từ maze (.map).
    Tab 2: chạy mô phỏng từ OSM (.osm) — tự build .net.xml + .rou.xml + .sumocfg
           vào Server/SUMO_xml/ rồi launch ở chế độ Custom Script.

Phần shared (dưới notebook): Run with GUI, Monitor, Start Server, Stop All —
dispatch theo tab đang active."""

import os
import sys
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog


class AppLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("SUMO-Unity System Launcher")
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

        # ── Tab 2 (OSM) vars ──────────────────────────────────────────
        self.osm_net_path = os.path.join(self.sumo_xml_dir, "HelloWorld.net.xml")
        self.osm_file = tk.StringVar()
        self.osm_mode = tk.StringVar(value="2d")
        self.osm_num_junctions = tk.StringVar(value="20")
        self.osm_edges_per_route = tk.StringVar(value="5")
        self.osm_algorithm = tk.StringVar(value="random")
        self.osm_gen_car = tk.BooleanVar(value=True)
        self.osm_gen_ped = tk.BooleanVar(value=True)
        self.osm_ped_impatience = tk.StringVar(value="0.5")

        # ── Shared vars ───────────────────────────────────────────────
        # Chế độ hiển thị realtime: 1 = chỉ 3D (Unity), 2 = cả 2D (sumo-gui) và 3D.
        self.gui_mode = tk.IntVar(value=1)
        self.server_process = None

        self._build_ui()
        self._toggle_mode()
        self._toggle_gui()
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

    # ═════════════════════════════════════════════════════════════════
    # UI scaffolding
    # ═════════════════════════════════════════════════════════════════

    def _build_ui(self):
        root_frame = ttk.Frame(self.root, padding=10)
        root_frame.pack(fill=tk.BOTH, expand=True)

        self.notebook = ttk.Notebook(root_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        maze_tab = ttk.Frame(self.notebook)
        osm_tab = ttk.Frame(self.notebook)
        self.notebook.add(maze_tab, text="Maze (.map) Simulation")
        self.notebook.add(osm_tab, text="OSM (.osm) Simulation")

        self._build_maze_tab(maze_tab)
        self._build_osm_tab(osm_tab)
        self._build_shared_section(root_frame)

    # ═════════════════════════════════════════════════════════════════
    # Tab 1 — Maze .map
    # ═════════════════════════════════════════════════════════════════

    def _build_maze_tab(self, parent):
        main_frame = ttk.Frame(parent, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_frame, text="Map Type:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Label(main_frame, text="Maze (.map)").grid(row=0, column=1, sticky=tk.W, padx=5)

        ttk.Label(main_frame, text="Map File (.map):").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.map_file, width=40).grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(main_frame, text="Browse", command=self._browse_map).grid(row=1, column=2, pady=5)

        ttk.Label(main_frame, text="Num Lanes (xe/bên):").grid(row=2, column=0, sticky=tk.W, pady=5)
        lane_frame = ttk.Frame(main_frame)
        lane_frame.grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
        ttk.Spinbox(lane_frame, from_=1, to=3, textvariable=self.num_lanes, width=10).pack(side=tk.LEFT)
        ttk.Label(lane_frame, text="(1–3 làn xe mỗi bên, +1 làn đi bộ)",
                  foreground="#666").pack(side=tk.LEFT, padx=6)

        ttk.Label(main_frame, text="Simulation Mode:").grid(row=3, column=0, sticky=tk.W, pady=5)
        mode_frame = ttk.Frame(main_frame)
        mode_frame.grid(row=3, column=1, sticky=tk.W)
        ttk.Radiobutton(mode_frame, text="1. Benchmark", variable=self.sim_mode,
                        value=1, command=self._toggle_mode).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(mode_frame, text="2. VRP", variable=self.sim_mode,
                        value=2, command=self._toggle_mode).pack(side=tk.LEFT, padx=5)

        ttk.Label(main_frame, text="Render Mode:").grid(row=4, column=0, sticky=tk.W, pady=5)
        render_frame = ttk.Frame(main_frame)
        render_frame.grid(row=4, column=1, sticky=tk.W)
        ttk.Radiobutton(render_frame, text="Realtime", variable=self.render_mode, value=1, command=self._toggle_gui).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(render_frame, text="Pre-render", variable=self.render_mode, value=2, command=self._toggle_gui).pack(side=tk.LEFT, padx=5)

        # Benchmark frame
        self.bench_frame = ttk.LabelFrame(main_frame, text="Benchmark Mode Options", padding=10)
        self.bench_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)

        ttk.Label(self.bench_frame, text="Number of Pairs:").grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Spinbox(self.bench_frame, from_=1, to=1000, textvariable=self.num_pairs, width=10).grid(row=0, column=1, sticky=tk.W, pady=2)

        ttk.Label(self.bench_frame, text="Car Crossroad Type:").grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Combobox(self.bench_frame, textvariable=self.car_cr_type,
                     values=["CS", "SS", "IO", "OI"], width=8, state="readonly").grid(row=1, column=1, sticky=tk.W, pady=2)

        ttk.Checkbutton(self.bench_frame, text="Create pedestrians?",
                        variable=self.has_ped, command=self._toggle_ped).grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=5)

        self.ped_cr_lbl = ttk.Label(self.bench_frame, text="Ped Crossroad Type:")
        self.ped_cr_lbl.grid(row=3, column=0, sticky=tk.W, pady=2)
        self.ped_cr_cb = ttk.Combobox(self.bench_frame, textvariable=self.ped_cr_type,
                                       values=["CS", "SS", "IO", "OI"], width=8, state="readonly")
        self.ped_cr_cb.grid(row=3, column=1, sticky=tk.W, pady=2)

        self.ped_imp_lbl = ttk.Label(self.bench_frame, text="Ped Impatience (0-1):")
        self.ped_imp_lbl.grid(row=4, column=0, sticky=tk.W, pady=2)
        self.ped_imp_sb = ttk.Spinbox(self.bench_frame, from_=0.0, to=1.0,
                                       increment=0.1, textvariable=self.ped_impatience, width=10)
        self.ped_imp_sb.grid(row=4, column=1, sticky=tk.W, pady=2)

        # VRP frame
        self.vrp_frame = ttk.LabelFrame(main_frame, text="VRP Mode Options", padding=10)
        self.vrp_frame.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)

        ttk.Label(self.vrp_frame, text="Number of Clients:").grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Spinbox(self.vrp_frame, from_=1, to=1000, textvariable=self.num_clients, width=10).grid(row=0, column=1, sticky=tk.W, pady=2)

        ttk.Label(self.vrp_frame, text="Number of Staff:").grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Spinbox(self.vrp_frame, from_=1, to=100, textvariable=self.num_staff, width=10).grid(row=1, column=1, sticky=tk.W, pady=2)

    def _browse_map(self):
        init_dir = os.path.join(self.server_dir, "map")
        if not os.path.exists(init_dir):
            init_dir = self.base_dir
        path = filedialog.askopenfilename(
            initialdir=init_dir, title="Select Map File",
            filetypes=[("Map Files", "*.map"), ("All Files", "*.*")],
        )
        if path:
            self.map_file.set(path)

    def _toggle_mode(self):
        if self.sim_mode.get() == 1:
            for child in self.bench_frame.winfo_children(): child.configure(state='normal')
            for child in self.vrp_frame.winfo_children(): child.configure(state='disabled')
            self._toggle_ped()
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
        else:
            self.ped_cr_lbl.configure(state='disabled')
            self.ped_cr_cb.configure(state='disabled')
            self.ped_imp_lbl.configure(state='disabled')
            self.ped_imp_sb.configure(state='disabled')

    # ═════════════════════════════════════════════════════════════════
    # Tab 2 — OSM .osm
    # ═════════════════════════════════════════════════════════════════

    def _build_osm_tab(self, parent):
        frame = ttk.Frame(parent, padding=15)
        frame.pack(fill=tk.BOTH, expand=True)
        frame.columnconfigure(1, weight=1)

        ttk.Label(frame, text="OSM File (.osm):").grid(row=0, column=0, sticky=tk.W, pady=4)
        ttk.Entry(frame, textvariable=self.osm_file).grid(row=0, column=1, columnspan=3, sticky=tk.EW, padx=5, pady=4)
        ttk.Button(frame, text="Browse", command=self._browse_osm).grid(row=0, column=4, pady=4)

        ttk.Label(frame, text="→ Output:", foreground="#555").grid(row=1, column=0, sticky=tk.W, pady=4)
        ttk.Label(frame, text=os.path.relpath(self.osm_net_path, self.base_dir) + " (+ .rou.xml + .sumocfg)",
                  foreground="#555").grid(row=1, column=1, columnspan=4, sticky=tk.W, padx=5)

        ttk.Separator(frame, orient=tk.HORIZONTAL).grid(row=2, column=0, columnspan=5, sticky=tk.EW, pady=8)

        ttk.Label(frame, text="Map mode:").grid(row=3, column=0, sticky=tk.W, pady=4)
        mode_frame = ttk.Frame(frame)
        mode_frame.grid(row=3, column=1, columnspan=4, sticky=tk.W)
        ttk.Radiobutton(mode_frame, text="2D (khuyến khích — bản đồ không có cầu vượt chồng chéo)",
                        variable=self.osm_mode, value="2d").pack(anchor=tk.W)
        ttk.Radiobutton(mode_frame, text="3D (giữ cao độ + cầu vượt — khi cần chính xác)",
                        variable=self.osm_mode, value="3d").pack(anchor=tk.W)

        ttk.Label(frame, text="Số junction:").grid(row=4, column=0, sticky=tk.W, pady=4)
        ttk.Entry(frame, textvariable=self.osm_num_junctions, width=10).grid(row=4, column=1, sticky=tk.W, padx=5, pady=4)
        ttk.Label(frame, text="(lấy tối đa nếu vượt số khả dụng)",
                  foreground="#666").grid(row=4, column=2, columnspan=3, sticky=tk.W)

        ttk.Label(frame, text="Độ dài tuyến:").grid(row=5, column=0, sticky=tk.W, pady=4)
        ttk.Entry(frame, textvariable=self.osm_edges_per_route, width=10).grid(row=5, column=1, sticky=tk.W, padx=5, pady=4)
        ttk.Label(frame, text="(số đoạn đường liên tiếp mỗi xe/người đi qua)",
                  foreground="#666").grid(row=5, column=2, columnspan=3, sticky=tk.W)

        ttk.Label(frame, text="Thuật toán:").grid(row=6, column=0, sticky=tk.W, pady=4)
        algo_frame = ttk.Frame(frame)
        algo_frame.grid(row=6, column=1, columnspan=4, sticky=tk.W)
        ttk.Radiobutton(algo_frame, text="Random (độ dài ngẫu nhiên 1..K, có thể dừng sớm)",
                        variable=self.osm_algorithm, value="random").pack(anchor=tk.W)
        ttk.Radiobutton(algo_frame, text="Maximum (cố gắng đủ K đoạn, có thể dừng sớm)",
                        variable=self.osm_algorithm, value="max").pack(anchor=tk.W)

        ttk.Label(frame, text="Sinh route cho:").grid(row=7, column=0, sticky=tk.W, pady=4)
        types_frame = ttk.Frame(frame)
        types_frame.grid(row=7, column=1, columnspan=4, sticky=tk.W)
        ttk.Checkbutton(types_frame, text="Xe", variable=self.osm_gen_car).pack(side=tk.LEFT, padx=(0, 12))
        ttk.Checkbutton(types_frame, text="Người đi bộ", variable=self.osm_gen_ped).pack(side=tk.LEFT, padx=(0, 12))
        ttk.Label(types_frame, text="Impatience:").pack(side=tk.LEFT)
        ttk.Entry(types_frame, textvariable=self.osm_ped_impatience, width=6).pack(side=tk.LEFT, padx=4)

        # Render Mode — share self.render_mode với Tab Maze để 2 tab đồng bộ
        ttk.Label(frame, text="Render Mode:").grid(row=8, column=0, sticky=tk.W, pady=4)
        render_frame = ttk.Frame(frame)
        render_frame.grid(row=8, column=1, columnspan=4, sticky=tk.W)
        ttk.Radiobutton(render_frame, text="Realtime", variable=self.render_mode, value=1, command=self._toggle_gui).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(render_frame, text="Pre-render", variable=self.render_mode, value=2, command=self._toggle_gui).pack(side=tk.LEFT, padx=5)

    def _browse_osm(self):
        init_dir = os.path.join(self.server_dir, "osm")
        if not os.path.isdir(init_dir):
            init_dir = self.base_dir
        path = filedialog.askopenfilename(
            initialdir=init_dir, title="Select OSM File",
            filetypes=[("OSM Files", "*.osm"), ("All Files", "*.*")],
        )
        if path:
            self.osm_file.set(path)

    # ═════════════════════════════════════════════════════════════════
    # Shared section (dưới notebook)
    # ═════════════════════════════════════════════════════════════════

    def _build_shared_section(self, parent):
        shared = ttk.Frame(parent, padding=(15, 10, 15, 5))
        shared.pack(fill=tk.X)

        gui_frame = ttk.Frame(shared)
        gui_frame.pack(anchor=tk.W, pady=(0, 5))
        ttk.Label(gui_frame, text="Chế độ hiển thị (Realtime):").pack(side=tk.LEFT, padx=(0, 8))
        self.gui_3d_rb = ttk.Radiobutton(gui_frame, text="Chỉ 3D", variable=self.gui_mode, value=1)
        self.gui_3d_rb.pack(side=tk.LEFT, padx=4)
        self.gui_2d3d_rb = ttk.Radiobutton(gui_frame, text="Cả 2D và 3D", variable=self.gui_mode, value=2)
        self.gui_2d3d_rb.pack(side=tk.LEFT, padx=4)

        monitor = ttk.LabelFrame(shared, text="Simulation Monitor", padding=10)
        monitor.pack(fill=tk.X, pady=5)
        self.status_lbl = ttk.Label(monitor, text="Status: IDLE",
                                    font=("Segoe UI", 10, "bold"), foreground="blue")
        self.status_lbl.grid(row=0, column=0, sticky=tk.W, pady=2)
        self.timestep_lbl = ttk.Label(monitor, text="Time Step: N/A", font=("Segoe UI", 10))
        self.timestep_lbl.grid(row=1, column=0, sticky=tk.W, pady=2)

        btn_frame = tk.Frame(shared)
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text="Start Server", font=("Segoe UI", 11, "bold"),
                  bg="#4CAF50", fg="white", width=15, command=self._start_server).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="Stop All", font=("Segoe UI", 11, "bold"),
                  bg="#f44336", fg="white", width=15, command=self._stop_all).pack(side=tk.LEFT, padx=10)

    # ═════════════════════════════════════════════════════════════════
    # Start Server — dispatch theo tab
    # ═════════════════════════════════════════════════════════════════

    def _start_server(self):
        if self.server_process and self.server_process.poll() is None:
            messagebox.showinfo("Info", "Server is already running!")
            return

        active = self.notebook.index(self.notebook.select())
        if active == 0:
            self._start_from_maze()
        else:
            self._start_from_osm()

    # ── Tab 1 path: maze .map ────────────────────────────────────────
    def _start_from_maze(self):
        if not self.map_file.get():
            messagebox.showerror("Error", "Hãy chọn 1 file .map.")
            return
        if not os.path.isfile(self.map_file.get()):
            messagebox.showerror("Error", "File .map không tồn tại.")
            return

        inputs = [str(self.sim_mode.get())]
        if self.sim_mode.get() == 1:
            inputs.append(str(self.num_pairs.get()))
            inputs.append(self.car_cr_type.get())
            inputs.append("y" if self.has_ped.get() else "n")
            if self.has_ped.get():
                inputs.append(self.ped_cr_type.get())
                inputs.append(str(self.ped_impatience.get()))
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
            messagebox.showerror("Error", "Hãy chọn 1 file .osm hợp lệ.")
            return
        if not (self.osm_gen_car.get() or self.osm_gen_ped.get()):
            messagebox.showerror("Error", "Phải chọn ít nhất 1 trong 'Xe' hoặc 'Người đi bộ'.")
            return
        try:
            n_junc = int(self.osm_num_junctions.get())
            k_edges = int(self.osm_edges_per_route.get())
            ped_imp = float(self.osm_ped_impatience.get())
        except ValueError:
            messagebox.showerror("Error", "Số junction / edges / impatience phải là số hợp lệ.")
            return
        if n_junc <= 0 or k_edges <= 0:
            messagebox.showerror("Error", "Số junction và edges/route phải > 0.")
            return

        os.makedirs(self.sumo_xml_dir, exist_ok=True)
        params = {
            "osm": osm, "out": self.osm_net_path, "mode": self.osm_mode.get(),
            "num_junctions": n_junc, "edges_per_route": k_edges,
            "algorithm": self.osm_algorithm.get(),
            "gen_car": self.osm_gen_car.get(), "gen_ped": self.osm_gen_ped.get(),
            "ped_impatience": ped_imp,
        }
        self.status_lbl.configure(text=f"Status: BUILDING OSM ({params['mode'].upper()})…",
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
            )
        except Exception as e:
            print(f"[Error] {e}")
            import traceback; traceback.print_exc()
            ok = False

        def after_build():
            if not ok:
                self.status_lbl.configure(text="Status: BUILD FAILED", foreground="red")
                messagebox.showerror(
                    "Failed",
                    "Build kịch bản OSM thất bại. Kiểm tra console (cần SUMO/netconvert trong PATH).",
                )
                return
            # Custom Script mode: pass folder path, main.py detect isdir
            inputs = [str(self.render_mode.get())]
            if self.render_mode.get() == 1:  # realtime mới cần chọn chế độ hiển thị
                inputs.append(str(self.gui_mode.get()))
            self._launch_main(self.sumo_xml_dir, self.num_lanes.get(), inputs)

        self.root.after(0, after_build)

    # ── Subprocess + monitor (chung cho cả 2 tab) ────────────────────
    def _launch_main(self, map_path, num_lanes, inputs):
        try:
            python_cmd = "python" if getattr(sys, 'frozen', False) else sys.executable
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"
            cmd = [python_cmd, "main.py", map_path, str(num_lanes)]
            self.server_process = subprocess.Popen(
                cmd, cwd=self.server_dir,
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1, encoding='utf-8', errors='replace', env=env,
            )
            self.server_process.stdin.write("\n".join(inputs) + "\n")
            self.server_process.stdin.flush()
            self.status_lbl.configure(text="Status: STARTING SERVER...", foreground="orange")
            threading.Thread(target=self._monitor_process, daemon=True).start()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start Server:\n{e}")

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
                    color = "green" if state == "PLAYING" else ("red" if state == "STOPPED" else "orange")
                    self.root.after(0, lambda s=state, c=color: self.status_lbl.configure(text=f"Status: {s}", foreground=c))
                elif "[MONITOR] TIME_STEP:" in line:
                    ts = line.split("TIME_STEP:")[1].strip()
                    self.root.after(0, lambda t=ts: self.timestep_lbl.configure(text=f"Time Step: {t}s"))
                elif "[MONITOR] CLIENT_CONNECTED" in line:
                    self.root.after(0, lambda: self.status_lbl.configure(text="Status: CLIENT CONNECTED, WAITING...", foreground="blue"))
        except Exception as e:
            print(f"Monitor thread error: {e}")
        self.root.after(0, lambda: self.status_lbl.configure(text="Status: STOPPED", foreground="red"))
        self.root.after(0, lambda: self.timestep_lbl.configure(text="Time Step: N/A"))

    def _stop_all(self):
        if self.server_process and self.server_process.poll() is None:
            self.server_process.terminate()
            self.server_process = None
            messagebox.showinfo("Info", "Stopped running processes.")
        else:
            messagebox.showinfo("Info", "No processes are currently running from Launcher.")

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
