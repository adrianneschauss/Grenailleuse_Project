import argparse
import csv
from pathlib import Path

from demo_composite_horizontal import demo_composite_flow


def export_positions(csv_path, env_time=None):
    csv_path = Path(csv_path)
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    with csv_path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["time", "segment", "item_id", "pos", "length"])
        last_time = {"t": None}

        def position_logger(t, segment_id, items, segment_length=None):
            if last_time["t"] != t:
                writer.writerow([f"{t:.3f}", "frame", "", "", ""])
                last_time["t"] = t
            for item in items:
                length_value = ""
                if segment_length is not None:
                    length_value = f"{segment_length:.4f}"
                writer.writerow(
                    [f"{t:.3f}", segment_id, item["id"], f"{item['pos']:.4f}", length_value]
                )

        demo_composite_flow(plot=False, env_time=env_time, position_logger=position_logger)


def main():
    parser = argparse.ArgumentParser(description="Export conveyor positions to CSV.")
    parser.add_argument("--out", default="positions.csv", help="Output CSV path")
    parser.add_argument("--env-time", type=float, default=None, help="Override env_time")
    args = parser.parse_args()

    export_positions(args.out, env_time=args.env_time)


if __name__ == "__main__":
    main()
