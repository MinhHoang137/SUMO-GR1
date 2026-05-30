"""Launcher phụ trợ: dựng kịch bản SUMO (.net.xml + .rou.xml + .sumocfg) từ .osm.

Pipeline:
    1. netconvert chuyển .osm → .net.xml (2D phẳng hoặc 3D giữ cao độ).
    2. Chọn ngẫu nhiên N junction từ network, mỗi junction sinh chuỗi K edges
       (cho xe và người đi bộ) theo thuật toán Random / Maximum.
    3. Ghi .rou.xml và .sumocfg cùng folder với .net.xml.

Output có thể chạy ngay trong launcher chính ở chế độ Custom Script
(trỏ vào folder chứa cặp file vừa sinh)."""

import os
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk


class OSMLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("OSM → SUMO Scenario Builder")
        self.root.geometry("620x440")
        self.root.resizable(True, False)

        self.osm_file = tk.StringVar()
        self.output_file = tk.StringVar()
        self.mode = tk.StringVar(value="2d")
        self.num_junctions = tk.StringVar(value="20")
        self.edges_per_route = tk.StringVar(value="5")
        self.algorithm = tk.StringVar(value="random")
        self.gen_car = tk.BooleanVar(value=True)
        self.gen_ped = tk.BooleanVar(value=True)
        self.ped_impatience = tk.StringVar(value="0.5")

        if getattr(sys, "frozen", False):
            self.base_dir = os.path.dirname(sys.executable)
        else:
            self.base_dir = os.path.abspath(os.path.dirname(__file__))
        self.server_dir = os.path.join(self.base_dir, "Server")

        self._busy = False
        self._build_ui()

    def _build_ui(self):
        frame = ttk.Frame(self.root, padding=15)
        frame.pack(fill=tk.BOTH, expand=True)
        frame.columnconfigure(1, weight=1)

        # --- File pickers ---
        ttk.Label(frame, text="OSM File (.osm):").grid(row=0, column=0, sticky=tk.W, pady=4)
        ttk.Entry(frame, textvariable=self.osm_file).grid(row=0, column=1, columnspan=3, sticky=tk.EW, padx=5, pady=4)
        ttk.Button(frame, text="Browse", command=self._browse_osm).grid(row=0, column=4, pady=4)

        ttk.Label(frame, text="Output (.net.xml):").grid(row=1, column=0, sticky=tk.W, pady=4)
        ttk.Entry(frame, textvariable=self.output_file).grid(row=1, column=1, columnspan=3, sticky=tk.EW, padx=5, pady=4)
        ttk.Button(frame, text="Save As", command=self._browse_output).grid(row=1, column=4, pady=4)

        ttk.Separator(frame, orient=tk.HORIZONTAL).grid(row=2, column=0, columnspan=5, sticky=tk.EW, pady=8)

        # --- Mode 2D/3D ---
        ttk.Label(frame, text="Map mode:").grid(row=3, column=0, sticky=tk.W, pady=4)
        mode_frame = ttk.Frame(frame)
        mode_frame.grid(row=3, column=1, columnspan=4, sticky=tk.W)
        ttk.Radiobutton(mode_frame, text="2D (khuyến khích — bản đồ không có cầu vượt chồng chéo)",
                        variable=self.mode, value="2d").pack(anchor=tk.W)
        ttk.Radiobutton(mode_frame, text="3D (giữ cao độ + cầu vượt — khi cần chính xác)",
                        variable=self.mode, value="3d").pack(anchor=tk.W)

        # --- Scenario params ---
        ttk.Label(frame, text="Số junction:").grid(row=4, column=0, sticky=tk.W, pady=4)
        ttk.Entry(frame, textvariable=self.num_junctions, width=10).grid(row=4, column=1, sticky=tk.W, padx=5, pady=4)
        ttk.Label(frame, text="(lấy tối đa nếu vượt số khả dụng)",
                  foreground="#666").grid(row=4, column=2, columnspan=3, sticky=tk.W)

        ttk.Label(frame, text="Độ dài tuyến:").grid(row=5, column=0, sticky=tk.W, pady=4)
        ttk.Entry(frame, textvariable=self.edges_per_route, width=10).grid(row=5, column=1, sticky=tk.W, padx=5, pady=4)
        ttk.Label(frame, text="(số đoạn đường liên tiếp mỗi xe/người đi qua)",
                  foreground="#666").grid(row=5, column=2, columnspan=3, sticky=tk.W)

        ttk.Label(frame, text="Thuật toán:").grid(row=6, column=0, sticky=tk.W, pady=4)
        algo_frame = ttk.Frame(frame)
        algo_frame.grid(row=6, column=1, columnspan=4, sticky=tk.W)
        ttk.Radiobutton(algo_frame, text="Random (độ dài ngẫu nhiên 1..K, có thể dừng sớm)",
                        variable=self.algorithm, value="random").pack(anchor=tk.W)
        ttk.Radiobutton(algo_frame, text="Maximum (cố gắng đủ K đoạn, có thể dừng sớm)",
                        variable=self.algorithm, value="max").pack(anchor=tk.W)

        # --- Object types ---
        ttk.Label(frame, text="Sinh route cho:").grid(row=7, column=0, sticky=tk.W, pady=4)
        types_frame = ttk.Frame(frame)
        types_frame.grid(row=7, column=1, columnspan=4, sticky=tk.W)
        ttk.Checkbutton(types_frame, text="Xe", variable=self.gen_car).pack(side=tk.LEFT, padx=(0, 12))
        ttk.Checkbutton(types_frame, text="Người đi bộ", variable=self.gen_ped).pack(side=tk.LEFT, padx=(0, 12))
        ttk.Label(types_frame, text="Impatience:").pack(side=tk.LEFT)
        ttk.Entry(types_frame, textvariable=self.ped_impatience, width=6).pack(side=tk.LEFT, padx=4)

        ttk.Separator(frame, orient=tk.HORIZONTAL).grid(row=8, column=0, columnspan=5, sticky=tk.EW, pady=8)

        # --- Status + action ---
        self.status_lbl = ttk.Label(frame, text="Status: IDLE",
                                    font=("Segoe UI", 10, "bold"), foreground="blue")
        self.status_lbl.grid(row=9, column=0, columnspan=5, sticky=tk.W, pady=4)

        info = ttk.Label(
            frame,
            text="Sau khi xong: .net.xml + .rou.xml + .sumocfg sẽ ở cùng folder.\n"
                 "Mở folder đó bằng launcher chính ở chế độ Custom Script để chạy mô phỏng.",
            foreground="#555",
            justify=tk.LEFT,
        )
        info.grid(row=10, column=0, columnspan=5, sticky=tk.W, pady=(0, 6))

        btn_frame = tk.Frame(frame)
        btn_frame.grid(row=11, column=0, columnspan=5, pady=6)
        tk.Button(btn_frame, text="Generate Map + Scenario",
                  font=("Segoe UI", 11, "bold"),
                  bg="#4CAF50", fg="white", width=26,
                  command=self._on_generate).pack()

    # ─── file pickers ───────────────────────────────────────────────────
    def _browse_osm(self):
        init_dir = os.path.join(self.server_dir, "osm")
        if not os.path.isdir(init_dir):
            init_dir = self.base_dir
        path = filedialog.askopenfilename(
            initialdir=init_dir,
            title="Select OSM File",
            filetypes=[("OSM Files", "*.osm"), ("All Files", "*.*")],
        )
        if path:
            self.osm_file.set(path)
            if not self.output_file.get():
                self.output_file.set(os.path.splitext(path)[0] + ".net.xml")

    def _browse_output(self):
        init_dir = self.base_dir
        if self.output_file.get():
            init_dir = os.path.dirname(self.output_file.get()) or init_dir
        path = filedialog.asksaveasfilename(
            initialdir=init_dir,
            title="Save .net.xml As",
            defaultextension=".net.xml",
            filetypes=[("SUMO Network", "*.net.xml"), ("All Files", "*.*")],
        )
        if path:
            self.output_file.set(path)

    # ─── action ─────────────────────────────────────────────────────────
    def _on_generate(self):
        if self._busy:
            return
        osm = self.osm_file.get()
        out = self.output_file.get() or (os.path.splitext(osm)[0] + ".net.xml" if osm else "")
        if not osm or not os.path.isfile(osm):
            messagebox.showerror("Error", "Hãy chọn 1 file .osm hợp lệ.")
            return
        if not out:
            messagebox.showerror("Error", "Hãy chọn đường dẫn output .net.xml.")
            return
        if not (self.gen_car.get() or self.gen_ped.get()):
            messagebox.showerror("Error", "Phải chọn ít nhất 1 trong 'Xe' hoặc 'Người đi bộ'.")
            return

        try:
            n_junc = int(self.num_junctions.get())
            k_edges = int(self.edges_per_route.get())
            ped_imp = float(self.ped_impatience.get())
        except ValueError:
            messagebox.showerror("Error",
                                 "Số junction / edges / impatience phải là số hợp lệ.")
            return
        if n_junc <= 0 or k_edges <= 0:
            messagebox.showerror("Error", "Số junction và edges/route phải > 0.")
            return

        params = {
            "osm": osm,
            "out": out,
            "mode": self.mode.get(),
            "num_junctions": n_junc,
            "edges_per_route": k_edges,
            "algorithm": self.algorithm.get(),
            "gen_car": self.gen_car.get(),
            "gen_ped": self.gen_ped.get(),
            "ped_impatience": ped_imp,
        }

        self._busy = True
        self.status_lbl.configure(text=f"Status: BUILDING ({params['mode'].upper()})…",
                                  foreground="orange")
        threading.Thread(target=self._run_build, args=(params,), daemon=True).start()

    def _run_build(self, params):
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
            ok = False
            print(f"[Error] {e}")
            import traceback
            traceback.print_exc()

        def done():
            self._busy = False
            if ok:
                folder = os.path.dirname(params["out"]) or "."
                self.status_lbl.configure(
                    text=f"Status: DONE → {os.path.basename(params['out'])}",
                    foreground="green",
                )
                messagebox.showinfo(
                    "Done",
                    f"Đã tạo xong kịch bản trong:\n{folder}\n\n"
                    "Mở folder này bằng launcher chính ở chế độ Custom Script để chạy.",
                )
            else:
                self.status_lbl.configure(text="Status: FAILED", foreground="red")
                messagebox.showerror(
                    "Failed",
                    "Build kịch bản thất bại. Kiểm tra console "
                    "(cần SUMO/netconvert trong PATH).",
                )

        self.root.after(0, done)


if __name__ == "__main__":
    root = tk.Tk()
    OSMLauncher(root)
    root.mainloop()
