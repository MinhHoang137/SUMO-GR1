from __future__ import annotations

import csv
import os
import sys


RENDER_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "render")
if RENDER_DIR not in sys.path:
	sys.path.insert(0, RENDER_DIR)


from result import VehicleTripCsvLogger


def main() -> None:
	out_path = os.path.join("result", "Simulation-test-avg.csv")
	if os.path.exists(out_path):
		os.remove(out_path)

	with VehicleTripCsvLogger(out_path) as logger:
		logger.on_step(0, departed_ids=["v1", "v2"], arrived_ids=[])
		logger.on_step(10, departed_ids=[], arrived_ids=["v1"])  # travel 10
		logger.on_step(20, departed_ids=[], arrived_ids=["v2"])  # travel 20

	with open(out_path, newline="", encoding="utf-8") as f:
		rows = list(csv.reader(f))

	print("header:", rows[0])
	print("last_row:", rows[-1])


if __name__ == "__main__":
	main()
