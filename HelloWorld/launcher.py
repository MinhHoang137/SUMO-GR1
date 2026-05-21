import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import subprocess
import os
import sys
import threading

class AppLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("SUMO-Unity System Launcher")
        self.root.geometry("500x650")
        self.root.resizable(True, True)
        
        # Variables
        self.map_type = tk.StringVar(value="map")  # "map" | "osm"
        self.map_file = tk.StringVar()
        self.num_lanes = tk.IntVar(value=2)
        self.sim_mode = tk.IntVar(value=1) # 1: Benchmark, 2: VRP
        
        # Benchmark variables
        self.num_pairs = tk.IntVar(value=20)
        self.car_cr_type = tk.StringVar(value="CS")
        self.has_ped = tk.BooleanVar(value=True)
        self.ped_cr_type = tk.StringVar(value="CS")
        self.ped_impatience = tk.DoubleVar(value=0.5)
        
        # VRP variables
        self.num_clients = tk.IntVar(value=10)
        self.num_staff = tk.IntVar(value=3)
        
        self.run_with_gui = tk.BooleanVar(value=True)
        self.render_mode = tk.IntVar(value=1) # 1: Realtime, 2: Pre-render
        
        self.server_process = None
        
        # Sửa lỗi đường dẫn khi build file .exe bằng PyInstaller
        if getattr(sys, 'frozen', False):
            self.base_dir = os.path.dirname(sys.executable)
        else:
            self.base_dir = os.path.abspath(os.path.dirname(__file__))
            
        self.server_dir = os.path.join(self.base_dir, "Server")
        
        self.build_ui()
        self.toggle_mode()
        
    def build_ui(self):
        main_frame = ttk.Frame(self.root, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Map Type
        ttk.Label(main_frame, text="Map Type:").grid(row=0, column=0, sticky=tk.W, pady=5)
        type_frame = ttk.Frame(main_frame)
        type_frame.grid(row=0, column=1, columnspan=2, sticky=tk.W)
        ttk.Radiobutton(type_frame, text="Maze (.map)", variable=self.map_type, value="map", command=self.toggle_map_type).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(type_frame, text="OSM (.osm)", variable=self.map_type, value="osm", command=self.toggle_map_type).pack(side=tk.LEFT, padx=5)

        # Map Selection
        self.map_file_lbl = ttk.Label(main_frame, text="Map File (.map):")
        self.map_file_lbl.grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.map_file, width=40).grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(main_frame, text="Browse", command=self.browse_map).grid(row=1, column=2, pady=5)

        # Lanes (chỉ áp dụng cho .map; .osm tự định nghĩa số làn)
        self.lanes_lbl = ttk.Label(main_frame, text="Num Lanes:")
        self.lanes_lbl.grid(row=2, column=0, sticky=tk.W, pady=5)
        self.lanes_sb = ttk.Spinbox(main_frame, from_=1, to=10, textvariable=self.num_lanes, width=10)
        self.lanes_sb.grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)

        # Mode
        ttk.Label(main_frame, text="Simulation Mode:").grid(row=3, column=0, sticky=tk.W, pady=5)
        mode_frame = ttk.Frame(main_frame)
        mode_frame.grid(row=3, column=1, sticky=tk.W)
        ttk.Radiobutton(mode_frame, text="1. Benchmark", variable=self.sim_mode, value=1, command=self.toggle_mode).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(mode_frame, text="2. VRP", variable=self.sim_mode, value=2, command=self.toggle_mode).pack(side=tk.LEFT, padx=5)

        # Render Mode
        ttk.Label(main_frame, text="Render Mode:").grid(row=4, column=0, sticky=tk.W, pady=5)
        render_frame = ttk.Frame(main_frame)
        render_frame.grid(row=4, column=1, sticky=tk.W)
        ttk.Radiobutton(render_frame, text="Realtime", variable=self.render_mode, value=1).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(render_frame, text="Pre-render", variable=self.render_mode, value=2).pack(side=tk.LEFT, padx=5)

        # --- Benchmark Frame ---
        self.bench_frame = ttk.LabelFrame(main_frame, text="Benchmark Mode Options", padding=10)
        self.bench_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        ttk.Label(self.bench_frame, text="Number of Pairs:").grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Spinbox(self.bench_frame, from_=1, to=1000, textvariable=self.num_pairs, width=10).grid(row=0, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(self.bench_frame, text="Car Crossroad Type:").grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Combobox(self.bench_frame, textvariable=self.car_cr_type, values=["CS", "SS", "IO", "OI"], width=8, state="readonly").grid(row=1, column=1, sticky=tk.W, pady=2)
        
        ttk.Checkbutton(self.bench_frame, text="Create pedestrians?", variable=self.has_ped, command=self.toggle_ped).grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        self.ped_cr_lbl = ttk.Label(self.bench_frame, text="Ped Crossroad Type:")
        self.ped_cr_lbl.grid(row=3, column=0, sticky=tk.W, pady=2)
        self.ped_cr_cb = ttk.Combobox(self.bench_frame, textvariable=self.ped_cr_type, values=["CS", "SS", "IO", "OI"], width=8, state="readonly")
        self.ped_cr_cb.grid(row=3, column=1, sticky=tk.W, pady=2)
        
        self.ped_imp_lbl = ttk.Label(self.bench_frame, text="Ped Impatience (0-1):")
        self.ped_imp_lbl.grid(row=4, column=0, sticky=tk.W, pady=2)
        self.ped_imp_sb = ttk.Spinbox(self.bench_frame, from_=0.0, to=1.0, increment=0.1, textvariable=self.ped_impatience, width=10)
        self.ped_imp_sb.grid(row=4, column=1, sticky=tk.W, pady=2)
        
        # --- VRP Frame ---
        self.vrp_frame = ttk.LabelFrame(main_frame, text="VRP Mode Options", padding=10)
        self.vrp_frame.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)

        ttk.Label(self.vrp_frame, text="Number of Clients:").grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Spinbox(self.vrp_frame, from_=1, to=1000, textvariable=self.num_clients, width=10).grid(row=0, column=1, sticky=tk.W, pady=2)

        ttk.Label(self.vrp_frame, text="Number of Staff:").grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Spinbox(self.vrp_frame, from_=1, to=100, textvariable=self.num_staff, width=10).grid(row=1, column=1, sticky=tk.W, pady=2)

        # --- Common Options ---
        ttk.Checkbutton(main_frame, text="Run with GUI (Start Unity Client Automatically)", variable=self.run_with_gui).grid(row=7, column=0, columnspan=3, sticky=tk.W, pady=10)

        # --- Monitor Frame ---
        self.monitor_frame = ttk.LabelFrame(main_frame, text="Simulation Monitor", padding=10)
        self.monitor_frame.grid(row=8, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)

        self.status_lbl = ttk.Label(self.monitor_frame, text="Status: IDLE", font=("Segoe UI", 10, "bold"), foreground="blue")
        self.status_lbl.grid(row=0, column=0, sticky=tk.W, pady=2)

        self.timestep_lbl = ttk.Label(self.monitor_frame, text="Time Step: N/A", font=("Segoe UI", 10))
        self.timestep_lbl.grid(row=1, column=0, sticky=tk.W, pady=2)

        # Buttons
        btn_frame = tk.Frame(main_frame)
        btn_frame.grid(row=9, column=0, columnspan=3, pady=15)
        
        tk.Button(btn_frame, text="Start Server", font=("Segoe UI", 11, "bold"), bg="#4CAF50", fg="white", width=15, command=self.start_server).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="Stop All", font=("Segoe UI", 11, "bold"), bg="#f44336", fg="white", width=15, command=self.stop_all).pack(side=tk.LEFT, padx=10)

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def browse_map(self):
        init_dir = os.path.join(self.server_dir, "map")
        if not os.path.exists(init_dir):
            init_dir = self.base_dir
        if self.map_type.get() == "osm":
            filetypes = [("OSM Files", "*.osm"), ("All Files", "*.*")]
            title = "Select OSM File"
        else:
            filetypes = [("Map Files", "*.map"), ("All Files", "*.*")]
            title = "Select Map File"
        path = filedialog.askopenfilename(initialdir=init_dir, title=title, filetypes=filetypes)
        if path:
            # Save absolute path
            self.map_file.set(path)

    def toggle_map_type(self):
        """Cập nhật label + bật/tắt Num Lanes theo loại map đang chọn (.osm tự định nghĩa số làn)."""
        if self.map_type.get() == "osm":
            self.map_file_lbl.configure(text="Map File (.osm):")
            self.lanes_lbl.configure(state="disabled")
            self.lanes_sb.configure(state="disabled")
        else:
            self.map_file_lbl.configure(text="Map File (.map):")
            self.lanes_lbl.configure(state="normal")
            self.lanes_sb.configure(state="normal")
        # Xoá đường dẫn cũ để tránh dùng nhầm file sai loại
        self.map_file.set("")

    def toggle_mode(self):
        if self.sim_mode.get() == 1: # Benchmark
            for child in self.bench_frame.winfo_children(): child.configure(state='normal')
            for child in self.vrp_frame.winfo_children(): child.configure(state='disabled')
            self.toggle_ped()
        else: # VRP
            for child in self.bench_frame.winfo_children(): child.configure(state='disabled')
            for child in self.vrp_frame.winfo_children(): child.configure(state='normal')

    def toggle_ped(self):
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
            
    def start_server(self):
        if not self.map_file.get():
            messagebox.showerror("Error", "Please select a Map file first.")
            return
            
        if self.server_process and self.server_process.poll() is None:
            messagebox.showinfo("Info", "Server is already running!")
            return
            
        # Build stdin inputs for main.py's input() prompts
        inputs = []
        inputs.append(str(self.sim_mode.get())) # 1: Benchmark, 2: VRP
        
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
            
        inputs.append("y" if self.run_with_gui.get() else "n")
        inputs.append(str(self.render_mode.get()))
        
        # Combine all answers with newlines
        input_str = "\n".join(inputs) + "\n"
        
        try:
            # Sửa lỗi gọi lại executable khi chạy file .exe
            python_cmd = "python" if getattr(sys, 'frozen', False) else sys.executable
            
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"
            
            # run command: python main.py <maze_file_path> <num_lanes>
            cmd = [python_cmd, "main.py", self.map_file.get(), str(self.num_lanes.get())]
            self.server_process = subprocess.Popen(
                cmd, 
                cwd=self.server_dir, 
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                encoding='utf-8',
                errors='replace',
                env=env
            )
            
            # Send inputs instantly directly to the console program
            self.server_process.stdin.write(input_str)
            self.server_process.stdin.flush()
            
            # Start monitor thread
            self.status_lbl.configure(text="Status: STARTING SERVER...", foreground="orange")
            threading.Thread(target=self.monitor_process, daemon=True).start()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start Server:\n{e}")

    def monitor_process(self):
        if not self.server_process:
            return
            
        try:
            for line in iter(self.server_process.stdout.readline, ''):
                line = line.strip()
                if not line:
                    continue
                
                # Print server output to launcher's console for debugging
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

    def stop_all(self):
        if self.server_process and self.server_process.poll() is None:
            self.server_process.terminate()
            self.server_process = None
            messagebox.showinfo("Info", "Stopped running processes.")
        else:
            messagebox.showinfo("Info", "No processes are currently running from Launcher.")

    def on_closing(self):
        # Force terminate on close
        if self.server_process and self.server_process.poll() is None:
            self.server_process.terminate()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = AppLauncher(root)
    root.mainloop()