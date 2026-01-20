import csv
import os
from pathlib import Path

from manim import AnimationGroup, ImageMobject, Line, Scene, VGroup, Dot, config


POSITIONS_CSV = os.environ.get("POSITIONS_CSV", "positions.csv")
BG_IMAGE = os.environ.get("BG_IMAGE", "")
TIME_SCALE = float(os.environ.get("TIME_SCALE", "0.05"))
MIN_FRAME_TIME = 0.02
DOT_RADIUS = 0.08

SEGMENTS = {
    "c1": {"start": (-5.5, 1.0, 0.0), "end": (5.5, 1.0, 0.0)},
    "c2": {"start": (-5.5, -1.0, 0.0), "end": (5.5, -1.0, 0.0)},
}


def load_frames(csv_path):
    frames = []
    current_time = None
    current_items = {}

    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            segment = row["segment"]
            if segment == "frame":
                if current_time is not None:
                    frames.append((current_time, current_items))
                current_time = float(row["time"])
                current_items = {}
                continue

            if current_time is None:
                current_time = float(row["time"])
            item_id = int(row["item_id"])
            pos = float(row["pos"])
            length = float(row["length"]) if row["length"] else None
            current_items[item_id] = (segment, pos, length)

    if current_time is not None:
        frames.append((current_time, current_items))

    return frames


def segment_position(segment_id, pos, length):
    segment = SEGMENTS.get(segment_id)
    if segment is None or length in (None, 0):
        return None
    start = segment["start"]
    end = segment["end"]
    ratio = max(0.0, min(1.0, pos / length))
    return (
        start[0] + (end[0] - start[0]) * ratio,
        start[1] + (end[1] - start[1]) * ratio,
        start[2] + (end[2] - start[2]) * ratio,
    )


class LineScene(Scene):
    def construct(self):
        csv_path = Path(POSITIONS_CSV)
        if not csv_path.exists():
            raise FileNotFoundError(f"CSV not found: {csv_path}")

        if BG_IMAGE:
            bg_path = Path(BG_IMAGE)
            if bg_path.exists():
                bg = ImageMobject(str(bg_path))
                bg.scale_to_fit_width(config.frame_width)
                bg.set_z_index(-1)
                self.add(bg)

        lines = VGroup(
            Line(SEGMENTS["c1"]["start"], SEGMENTS["c1"]["end"]),
            Line(SEGMENTS["c2"]["start"], SEGMENTS["c2"]["end"]),
        )
        lines.set_stroke(width=4, opacity=0.4)
        self.add(lines)

        frames = load_frames(str(csv_path))
        if len(frames) < 2:
            return

        dots = {}

        for idx in range(len(frames) - 1):
            t_now, items_now = frames[idx]
            t_next, _ = frames[idx + 1]
            dt = max((t_next - t_now) * TIME_SCALE, MIN_FRAME_TIME)
            animations = []

            for item_id, (segment_id, pos, length) in items_now.items():
                target = segment_position(segment_id, pos, length)
                if target is None:
                    continue
                if item_id not in dots:
                    dot = Dot(point=target, radius=DOT_RADIUS)
                    dots[item_id] = dot
                    self.add(dot)
                animations.append(dots[item_id].animate.move_to(target).set_opacity(1.0))

            for item_id, dot in dots.items():
                if item_id not in items_now:
                    animations.append(dot.animate.set_opacity(0.0))

            if animations:
                self.play(AnimationGroup(*animations, lag_ratio=0), run_time=dt)
            else:
                self.wait(dt)
