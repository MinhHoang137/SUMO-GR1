from __future__ import annotations

import csv
import json
import os
from datetime import datetime
from dataclasses import dataclass
from typing import Iterable


def build_simulation_summary_json_path(csv_path: str) -> str:
    """Build a summary .json path that matches a simulation CSV name.

    Example:
        result/Simulation-2026-02-04-15-30-05.csv -> result/Simulation-2026-02-04-15-30-05.json
    """
    root, _ext = os.path.splitext(csv_path)
    return f"{root}.json"


def finish_simulation_logging(
    trip_logger: "VehicleTripCsvLogger",
    ped_count: int,
    ped_impatience: float | None,
    map_name: str | None,
    summary_path: str | None = None,
) -> None:
    """Closes the CSV logger and writes the simulation summary JSON file.

    If *summary_path* is given it is used directly; otherwise the path is
    derived from the CSV path by replacing the extension with .json.
    """
    try:
        trip_logger.close()
    except Exception as e:
        print(f"Error closing CSV trip logger: {e}")

    try:
        if summary_path is None:
            summary_path = build_simulation_summary_json_path(trip_logger.csv_path)
        write_simulation_summary_json(
            summary_path,
            vehicle_count=trip_logger.vehicle_trip_count,
            pedestrian_count=ped_count,
            avg_vehicle_travel_steps=trip_logger.avg_travel_steps,
            pedestrian_impatience=ped_impatience,
            map_name=map_name,
        )
        print(f"Simulation summary written: {summary_path}")
    except Exception as e:
        print(f"Error writing simulation summary JSON: {e}")


def write_simulation_summary_json(
    json_path: str,
    *,
    vehicle_count: int,
    pedestrian_count: int,
    avg_vehicle_travel_steps: float,
    pedestrian_impatience: float | None,
    map_name: str | None,
) -> None:
    """Write a machine-readable simulation summary to a .json file."""
    directory = os.path.dirname(json_path)
    if directory:
        os.makedirs(directory, exist_ok=True)

    payload = {
        "vehicles": int(vehicle_count),
        "pedestrians": int(pedestrian_count),
        "avg_vehicle_travel_steps": avg_vehicle_travel_steps,
        "pedestrian_impatience": pedestrian_impatience,
        "map_name": map_name,
    }

    with open(json_path, mode="w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


@dataclass(frozen=True)
class VehicleTripRow:
    vehicle_id: str
    depart_step: int
    arrival_step: int

    @property
    def travel_steps(self) -> int:
        return self.arrival_step - self.depart_step


class VehicleTripCsvLogger:
    """Log vehicle trip info (depart/arrive in steps) to CSV.

    Usage:
        logger = VehicleTripCsvLogger("result/vehicle_trips.csv")
        logger.open()
        ... each simulation step ...
        logger.on_step(step_index, departed_ids, arrived_ids)
        ...
        logger.close()
    """

    def __init__(self, csv_path: str = "result/vehicle_trips.csv"):
        self._csv_path = csv_path
        self._file = None
        self._writer = None
        self._depart_step_by_vehicle: dict[str, int] = {}
        self._travel_steps_sum: int = 0
        self._travel_steps_count: int = 0

    @property
    def csv_path(self) -> str:
        return self._csv_path

    @property
    def vehicle_trip_count(self) -> int:
        return int(self._travel_steps_count)

    @property
    def avg_travel_steps(self) -> float:
        if self._travel_steps_count <= 0:
            return -1
        return self._travel_steps_sum / self._travel_steps_count

    def open(self) -> None:
        directory = os.path.dirname(self._csv_path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        self._file = open(self._csv_path, mode="w", newline="", encoding="utf-8")
        self._writer = csv.writer(self._file)
        self._writer.writerow(["vehicle_id", "depart_step", "arrival_step", "travel_steps"])
        self._travel_steps_sum = 0
        self._travel_steps_count = 0

    def close(self) -> None:
        if self._file is not None:
            try:
                if self._writer is not None:
                    avg_travel_steps: float
                    if self._travel_steps_count > 0:
                        avg_travel_steps = self._travel_steps_sum / self._travel_steps_count
                    else:
                        avg_travel_steps = -1
                    self._writer.writerow(["avg", -1, -1, avg_travel_steps])
                    self._file.flush()
            finally:
                self._file.close()
                self._file = None
                self._writer = None

    def __enter__(self) -> "VehicleTripCsvLogger":
        self.open()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def log_step(self, traci, step_index: int) -> list[VehicleTripRow]:
        """Convenience method to log a simulation step using the traci module directly."""
        return self.on_step(
            step_index,
            traci.simulation.getDepartedIDList(),
            traci.simulation.getArrivedIDList(),
        )

    def on_step(
        self, step_index: int, departed_ids: Iterable[str], arrived_ids: Iterable[str]
    ) -> list[VehicleTripRow]:
        """Update logger for a simulation step.

        Returns list of rows written in this step (useful for debugging/UI).
        """
        if self._writer is None:
            raise RuntimeError("VehicleTripCsvLogger is not open().")

        for vehicle_id in departed_ids or []:
            if vehicle_id not in self._depart_step_by_vehicle:
                self._depart_step_by_vehicle[vehicle_id] = int(step_index)

        written: list[VehicleTripRow] = []
        for vehicle_id in arrived_ids or []:
            depart_step = self._depart_step_by_vehicle.pop(vehicle_id, None)
            if depart_step is None:
                continue
            row = VehicleTripRow(
                vehicle_id=str(vehicle_id),
                depart_step=int(depart_step),
                arrival_step=int(step_index),
            )
            self._writer.writerow(
                [row.vehicle_id, row.depart_step, row.arrival_step, row.travel_steps]
            )
            self._travel_steps_sum += int(row.travel_steps)
            self._travel_steps_count += 1
            written.append(row)

        self._file.flush()
        return written
