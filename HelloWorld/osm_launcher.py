"""Launcher phụ trợ: dựng bản đồ 3D (.net.xml) từ tệp OpenStreetMap (.osm).

Đây KHÔNG phải launcher mô phỏng. Output (.net.xml) có thể mở/tinh chỉnh bằng
netedit, rồi đóng gói thành kịch bản và chạy qua launcher chính ở chế độ
Custom Script."""

import os
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk


class OSMLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("OSM → 3D Map Builder")
        self.root.geometry("520x260")
        self.root.resizable(True, False)

        self.osm_file = tk.StringVar()
        self.output_file = tk.StringVar()

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

        ttk.Label(frame, text="OSM File (.osm):").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(frame, textvariable=self.osm_file, width=46).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(frame, text="Browse", command=self._browse_osm).grid(row=0, column=2, pady=5)

        ttk.Label(frame, text="Output (.net.xml):").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(frame, textvariable=self.output_file, width=46).grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(frame, text="Save As", command=self._browse_output).grid(row=1, column=2, pady=5)

        self.status_lbl = ttk.Label(frame, text="Status: IDLE", font=("Segoe UI", 10, "bold"), foreground="blue")
        self.status_lbl.grid(row=2, column=0, columnspan=3, sticky=tk.W, pady=15)

        info = ttk.Label(
            frame,
            text="Sau khi tạo xong, mở .net.xml trong netedit để chỉnh sửa,\n"
                 "thêm route (.rou.xml) và sumocfg, rồi chạy launcher chính ở chế độ Custom Script.",
            foreground="#555",
            justify=tk.LEFT,
        )
        info.grid(row=3, column=0, columnspan=3, sticky=tk.W, pady=(0, 10))

        btn_frame = tk.Frame(frame)
        btn_frame.grid(row=4, column=0, columnspan=3, pady=5)
        tk.Button(btn_frame, text="Generate 3D Map", font=("Segoe UI", 11, "bold"),
                  bg="#4CAF50", fg="white", width=20, command=self._on_generate).pack()

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

        self._busy = True
        self.status_lbl.configure(text="Status: CONVERTING…", foreground="orange")
        threading.Thread(target=self._run_conversion, args=(osm, out), daemon=True).start()

    def _run_conversion(self, osm, out):
        # Import lười: osm_to_net cần subprocess gọi netconvert (SUMO PATH)
        if self.server_dir not in sys.path:
            sys.path.insert(0, self.server_dir)
        try:
            from osm_to_net import convert_osm_to_net_3d_roads
            ok = convert_osm_to_net_3d_roads(osm, out)
        except Exception as e:
            ok = False
            print(f"[Error] {e}")

        def done():
            self._busy = False
            if ok:
                self.status_lbl.configure(text=f"Status: DONE → {os.path.basename(out)}", foreground="green")
                messagebox.showinfo("Done", f"Đã tạo bản đồ 3D:\n{out}")
            else:
                self.status_lbl.configure(text="Status: FAILED", foreground="red")
                messagebox.showerror("Failed", "Chuyển đổi OSM thất bại. Kiểm tra console (cần SUMO/netconvert trong PATH).")

        self.root.after(0, done)


if __name__ == "__main__":
    root = tk.Tk()
    OSMLauncher(root)
    root.mainloop()
