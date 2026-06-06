import json
import os
from datetime import datetime


class SimulationSession:
    """Manages all output files for one simulation run in a single directory.

    Directory layout: result/{map_base_name}-{timestamp}/
        trips.csv (or trips-ped.csv)  — vehicle trip log
        summary.json                  — simulation summary
        road_data.json                — junction / edge / crossing data
        scenario.json                 — per-step simulation frames
    """

    MAX_BUFFER_SIZE = 10 * 1024 * 1024  # 10 MB

    def __init__(self, map_file: str, has_ped: bool = False):
        ts = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        map_base_name = os.path.splitext(os.path.basename(map_file))[0]
        self._session_dir = os.path.join("result", f"{map_base_name}-{ts}")

        ped_suffix = "-ped" if has_ped else ""
        self.csv_path = os.path.join(self._session_dir, f"trips{ped_suffix}.csv")
        self.summary_path = os.path.join(self._session_dir, "summary.json")
        self.road_data_path = os.path.join(self._session_dir, "road_data.json")
        self.scenario_path = os.path.join(self._session_dir, "scenario.json")

        self._out_file = None
        self._buffer: list[str] = []
        self._buffer_size = 0
        self._first_frame = True

    @property
    def session_dir(self) -> str:
        return self._session_dir

    def open(self) -> None:
        """Open the scenario JSON file for streaming writes."""
        os.makedirs(self._session_dir, exist_ok=True)
        self._out_file = open(self.scenario_path, "w", encoding="utf-8")
        self._out_file.write("[\n")
        self._first_frame = True
        self._buffer = []
        self._buffer_size = 0

    def save_road_data(self, road_data: dict) -> None:
        """Write road data (junctions, edges, crossings) to road_data.json."""
        os.makedirs(self._session_dir, exist_ok=True)
        with open(self.road_data_path, "w", encoding="utf-8") as f:
            json.dump(road_data, f, ensure_ascii=False, separators=(',', ':'))
        print(f"Road data saved to: {self.road_data_path}")

    def record_frame(self, data: dict) -> None:
        """Buffer one simulation frame; flushes automatically when buffer is full."""
        if self._out_file is None:
            return
        data_str = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
        self._buffer.append(data_str)
        self._buffer_size += len(data_str.encode("utf-8"))
        if self._buffer_size >= self.MAX_BUFFER_SIZE:
            self._flush_buffer()

    def _flush_buffer(self) -> None:
        if not self._buffer or self._out_file is None:
            return
        for item_str in self._buffer:
            if not self._first_frame:
                self._out_file.write(",\n")
            self._out_file.write(item_str)
            self._first_frame = False
        self._buffer.clear()
        self._buffer_size = 0

    def close(self) -> None:
        """Flush remaining frames, close the scenario JSON, and print paths."""
        if self._out_file is None:
            return
        self._flush_buffer()
        self._out_file.write("\n]")
        self._out_file.close()
        self._out_file = None
        print(f"Scenario saved to: {self.scenario_path}")
        print(f"Session directory: {self._session_dir}")
