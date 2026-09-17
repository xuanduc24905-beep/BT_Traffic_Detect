"""Người 2 — Line/zone counter với chống đếm trùng bằng tracking ID.

Ý tưởng: với mỗi ID, lưu tâm box của frame trước. Nếu segment nối tâm cũ → tâm
mới cắt qua counting line, ID đó được đếm 1 lần cho line đó và ghi nhớ vào set
đã-đếm để không đếm lại (kể cả nếu qua lại nhiều lần).
"""
import json
from collections import defaultdict
from dataclasses import dataclass, field


@dataclass
class Line:
    name: str
    p1: tuple  # (x, y)
    p2: tuple
    count_direction: str = "both"  # 'both' | 'ltr' | 'rtl'


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


@dataclass
class Counter:
    lines: list[Line]
    # counts[line_name][class_id] = int
    counts: dict = field(default_factory=lambda: defaultdict(lambda: defaultdict(int)))
    # đã đếm để tránh trùng: {(line_name, track_id)}
    _counted: set = field(default_factory=set)
    # tâm frame trước: {track_id: (x, y)}
    _prev_center: dict = field(default_factory=dict)

    def update(self, frame_idx: int, boxes_xyxy, ids, classes):
        """Gọi mỗi frame với box + id + class từ tracker."""
        for xyxy, tid, cls in zip(boxes_xyxy, ids, classes):
            if tid is None:
                continue
            tid = int(tid)
            cls = int(cls)
            cx = (xyxy[0] + xyxy[2]) / 2
            cy = (xyxy[1] + xyxy[3]) / 2

            prev = self._prev_center.get(tid)
            if prev is not None:
                for line in self.lines:
                    key = (line.name, tid)
                    if key in self._counted:
                        continue
                    if _segments_cross(prev, (cx, cy), line.p1, line.p2):
                        # TODO: nếu cần lọc chiều đi (ltr/rtl), check dấu cross-product
                        self.counts[line.name][cls] += 1
                        self._counted.add(key)
            self._prev_center[tid] = (cx, cy)

    def to_dict(self) -> dict:
        return {ln: dict(cnt) for ln, cnt in self.counts.items()}

    def total(self) -> int:
        return sum(sum(c.values()) for c in self.counts.values())
