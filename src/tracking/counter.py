"""Người 2 — Line/zone counter với chống đếm trùng bằng tracking ID.

Ý tưởng: với mỗi ID, lưu tâm box của frame trước. Nếu segment nối tâm cũ tâm
mới cắt qua counting line, ID đó được đếm 1 lần cho line đó và ghi nhớ vào set
đã-đếm để không đếm lại (kể cả nếu qua lại nhiều lần).

Hướng đi (direction):
  - Với mỗi line có vector v = p2 - p1, ta lấy dấu cross-product
    (v × movement) để phân loại hướng qua line:
      cross > 0 'ltr' (tráiphải theo chiều v)
      cross < 0 'rtl' (phảitrái theo chiều v)
  - Line có count_direction ∈ {'both','ltr','rtl'} để chỉ đếm 1 chiều.
"""
import json
from collections import defaultdict
from dataclasses import dataclass, field


@dataclass
class Line:
    name: str
    p1: tuple # (x, y)
    p2: tuple
    count_direction: str = "both" # 'both' | 'ltr' | 'rtl'


def load_lines(config_path: str, video_key: str) -> list[Line]:
    with open(config_path) as f:
        cfg = json.load(f)
    lines = []
    for l in cfg[video_key]["lines"]:
        lines.append(Line(name=l["name"], p1=tuple(l["points"][0]),
                          p2=tuple(l["points"][1]),
                          count_direction=l.get("count_direction", "both")))
    return lines


def _segments_cross(a1, a2, b1, b2) -> bool:
    """Trả True nếu segment a1-a2 và b1-b2 cắt nhau."""
    def ccw(p, q, r):
        return (r[1] - p[1]) * (q[0] - p[0]) > (q[1] - p[1]) * (r[0] - p[0])
    return (ccw(a1, b1, b2) != ccw(a2, b1, b2)
            and ccw(a1, a2, b1) != ccw(a1, a2, b2))


def _crossing_direction(prev, curr, line: Line) -> str:
    """Trả 'ltr' hoặc 'rtl' dựa trên dấu cross-product của line-vector × movement-vector."""
    vx = line.p2[0] - line.p1[0]
    vy = line.p2[1] - line.p1[1]
    mx = curr[0] - prev[0]
    my = curr[1] - prev[1]
    cross = vx * my - vy * mx
    return "ltr" if cross > 0 else "rtl"


@dataclass
class Counter:
    lines: list[Line]
    # counts[line_name][direction][class_id] = int (direction ∈ {'ltr','rtl'})
    counts: dict = field(default_factory=lambda: defaultdict(
        lambda: defaultdict(lambda: defaultdict(int))))
    # đã đếm để tránh trùng: {(line_name, track_id)}
    _counted: set = field(default_factory=set)
    # tâm frame trước: {track_id: (x, y)}
    _prev_center: dict = field(default_factory=dict)
    # sự kiện đếm chi tiết trong lần update gần nhất
    # phần tử: {"line", "direction", "track_id", "class_id"}
    _last_events: list = field(default_factory=list)

    def update(self, frame_idx: int, boxes_xyxy, ids, classes):
        """Gọi mỗi frame với box + id + class từ tracker.

        Trả về list các event vừa đếm trong frame này để caller (pipeline)
        có thể log ra CSV với track_id + direction thật.
        """
        events = []
        for xyxy, tid, cls in zip(boxes_xyxy, ids, classes):
            if tid is None:
                continue
            tid = int(tid)
            cls = int(cls)
            cx = (xyxy[0] + xyxy[2]) / 2
            cy = (xyxy[1] + xyxy[3]) / 2

            prev = self._prev_center.get(tid)
            if prev is not None:
                curr = (cx, cy)
                for line in self.lines:
                    key = (line.name, tid)
                    if key in self._counted:
                        continue
                    if not _segments_cross(prev, curr, line.p1, line.p2):
                        continue
                    direction = _crossing_direction(prev, curr, line)
                    if line.count_direction != "both" and line.count_direction != direction:
                        # đi ngược chiều cấu hình — vẫn đánh dấu để không đếm sau này
                        self._counted.add(key)
                        continue
                    self.counts[line.name][direction][cls] += 1
                    self._counted.add(key)
                    events.append({
                        "line": line.name,
                        "direction": direction,
                        "track_id": tid,
                        "class_id": cls,
                    })
            self._prev_center[tid] = (cx, cy)
        self._last_events = events
        return events

    def to_dict(self) -> dict:
        """Trả dict lồng: {line: {direction: {class_id: count}}}."""
        return {ln: {d: dict(c) for d, c in dirs.items()}
                for ln, dirs in self.counts.items()}

    def totals_per_line(self) -> dict:
        """{line: total_count} (gộp hết hướng và class)."""
        return {ln: sum(sum(c.values()) for c in dirs.values())
                for ln, dirs in self.counts.items()}

    def total(self) -> int:
        return sum(self.totals_per_line().values())
