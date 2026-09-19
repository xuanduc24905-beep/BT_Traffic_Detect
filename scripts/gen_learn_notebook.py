"""Sinh notebooks/learn_pipeline_from_scratch.ipynb — notebook học pipeline từ đầu.

Khác với demo_full_pipeline.ipynb (dùng import từ src/), notebook này viết
FULL CODE INLINE từng phần để nhóm đọc hiểu:
- Không dùng from src.pipeline.run
- Không dùng from src.tracking.counter
- Không dùng from src.stats.aggregator
Tự implement inline mọi thứ trong 1 file — vừa học vừa chạy.

Chạy: python scripts/gen_learn_notebook.py
"""
import json
from pathlib import Path

OUT = Path("notebooks/learn_pipeline_from_scratch.ipynb")
OUT.parent.mkdir(parents=True, exist_ok=True)


def md(text):
    return {"cell_type": "markdown", "metadata": {},
            "source": text.strip().splitlines(keepends=True)}


def code(src):
    return {"cell_type": "code", "execution_count": None, "metadata": {},
            "outputs": [], "source": src.strip().splitlines(keepends=True)}


CELLS = [
    # ============ TITLE ============
    md("""
# Học Pipeline Đếm Xe từ Đầu (Full Code)

**Chủ đề 10 — Notebook học từng bước, KHÔNG dùng import từ src/**

Notebook này viết **toàn bộ code inline** để nhóm đọc hiểu cách hệ thống hoạt động ở mức chi tiết nhất. Sau khi hiểu xong, có thể dùng version tối ưu ở `notebooks/demo_full_pipeline.ipynb` (import từ `src/`).

Cấu trúc 10 phần:
1. Setup + đọc video
2. Load YOLOv8 model detect 1 frame hiểu output tensor
3. Vẽ bounding box thủ công lên frame
4. Tracking với ByteTrack hiểu track_id
5. **Implement Counter class từ đầu** (segment intersection + cross-product)
6. Vòng lặp chính: detect + track + count qua toàn bộ video
7. Ghi video output có overlay + CSV events
8. Aggregate stats bằng pandas inline
9. Vẽ biểu đồ matplotlib inline
10. Evaluation: accuracy, MAE, MAPE inline

Yêu cầu: `pip install ultralytics opencv-python pandas matplotlib` + `weights/v8s_4cls_best.pt`.
"""),

    # ============ 1. SETUP ============
    md("""
---
## Phần 1 — Setup + Đọc video

Trước khi bắt đầu, kiểm tra môi trường và load video để biết resolution + fps + tổng frame.
"""),
    code("""
from pathlib import Path
import cv2
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

# Điều chỉnh path nếu cần
PROJECT_ROOT = Path.cwd()
if PROJECT_ROOT.name == "notebooks":
    PROJECT_ROOT = PROJECT_ROOT.parent

VIDEO_PATH = PROJECT_ROOT / "data/test_videos/raw/demo_traffic.mp4"
MODEL_PATH = PROJECT_ROOT / "weights/v8s_4cls_best.pt"

print(f"Project root: {PROJECT_ROOT}")
print(f"Video exists: {VIDEO_PATH.exists()}")
print(f"Model exists: {MODEL_PATH.exists()}")
"""),
    code("""
# Mở video, đọc metadata
cap = cv2.VideoCapture(str(VIDEO_PATH))
FPS = cap.get(cv2.CAP_PROP_FPS)
W = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
H = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
N_FRAMES = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
cap.release()

print(f"Video: {W}x{H}")
print(f"FPS: {FPS}")
print(f"Số frame: {N_FRAMES}")
print(f"Thời lượng: {N_FRAMES/FPS:.2f} giây")
"""),

    # ============ 2. DETECT 1 FRAME ============
    md("""
---
## Phần 2 — Detect 1 frame để hiểu output

Trước khi chạy pipeline full video, hãy detect thử 1 frame để biết **output của YOLO trông như thế nào**.

YOLO.predict() trả về `Results` object có:
- `results.boxes.xyxy` — tensor (N, 4) toạ độ bbox pixel
- `results.boxes.cls` — tensor (N,) class id
- `results.boxes.conf` — tensor (N,) confidence [0,1]
"""),
    code("""
from ultralytics import YOLO

model = YOLO(str(MODEL_PATH))
print("Model class names:", model.names)
"""),
    code("""
# Lấy frame đầu tiên
cap = cv2.VideoCapture(str(VIDEO_PATH))
ret, frame = cap.read() # frame là numpy array BGR (H, W, 3)
cap.release()

print(f"Frame shape: {frame.shape}, dtype: {frame.dtype}")

# Predict với conf=0.3 (bỏ box có confidence < 0.3)
results = model.predict(frame, conf=0.3, verbose=False)[0]

print(f"\\nSố box detect được: {len(results.boxes)}")
print(f"\\nBoxes xyxy (5 đầu):\\n{results.boxes.xyxy[:5]}")
print(f"\\nClasses (5 đầu): {results.boxes.cls[:5]}")
print(f"\\nConfidence (5 đầu): {results.boxes.conf[:5]}")
"""),
    code("""
# In ra danh sách detection với tên class
for i, (box, cls, conf) in enumerate(zip(results.boxes.xyxy, results.boxes.cls, results.boxes.conf)):
    x1, y1, x2, y2 = box.cpu().numpy().astype(int)
    cname = model.names[int(cls)]
    print(f"[{i:2d}] {cname:10s} conf={conf:.2f} box=({x1},{y1})-({x2},{y2})")
"""),

    # ============ 3. VẼ BOX ============
    md("""
---
## Phần 3 — Vẽ bounding box thủ công lên frame

Không dùng `results.plot()` — tự vẽ bằng `cv2.rectangle` và `cv2.putText` để hiểu cách bounding box được render.

**Note**: OpenCV dùng **BGR** (không phải RGB). Matplotlib thì dùng RGB — nên phải convert khi plot.
"""),
    code("""
# Vẽ box thủ công
frame_annotated = frame.copy()

for box, cls, conf in zip(results.boxes.xyxy, results.boxes.cls, results.boxes.conf):
    x1, y1, x2, y2 = box.cpu().numpy().astype(int)
    cname = model.names[int(cls)]

    # Vẽ rectangle: (frame, top_left, bottom_right, color_BGR, thickness)
    cv2.rectangle(frame_annotated, (x1, y1), (x2, y2), (0, 255, 0), 2)

    # Vẽ label
    label = f"{cname} {conf:.2f}"
    cv2.putText(frame_annotated, label, (x1, max(0, y1 - 6)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

# Hiển thị (convert BGR RGB cho matplotlib)
fig, ax = plt.subplots(figsize=(14, 8))
ax.imshow(cv2.cvtColor(frame_annotated, cv2.COLOR_BGR2RGB))
ax.set_title(f"Frame với {len(results.boxes)} bounding box")
ax.axis("off")
plt.tight_layout()
plt.show()
"""),

    # ============ 4. TRACKING ============
    md("""
---
## Phần 4 — Tracking để hiểu `track_id`

`model.predict()` không có `track_id`. Muốn theo dõi xe qua nhiều frame phải dùng `model.track()`.

Ultralytics tích hợp sẵn 2 tracker: **ByteTrack** và **BoT-SORT**. Ta dùng ByteTrack (SOTA 2022).

**Điểm mới**: mỗi box giờ có thêm `results.boxes.id` — track_id duy nhất cho mỗi xe.
"""),
    code("""
# Track thử 20 frame đầu, xem track_id thay đổi thế nào
cap = cv2.VideoCapture(str(VIDEO_PATH))

# Reset model tracker state (quan trọng nếu chạy nhiều lần)
model = YOLO(str(MODEL_PATH))

track_history = [] # lưu (frame_idx, list of track_ids)

for i in range(20):
    ret, frame = cap.read()
    if not ret:
        break
    # persist=True: giữ track qua các lần gọi
    res = model.track(frame, tracker="bytetrack.yaml", persist=True,
                       conf=0.3, verbose=False)[0]
    ids = res.boxes.id.cpu().numpy().astype(int).tolist() if res.boxes.id is not None else []
    track_history.append((i, ids))

cap.release()

print("Track IDs qua từng frame:")
for f_idx, ids in track_history[:10]:
    print(f" Frame {f_idx:3d}: {ids}")

# Đếm số track ID unique
all_ids = set()
for _, ids in track_history:
    all_ids.update(ids)
print(f"\\nTổng track_id unique trong 20 frame: {len(all_ids)}")
"""),
    md("""
**Nhận xét**: track_id được **giữ nguyên** cho cùng 1 xe qua các frame liên tiếp. ID chỉ tăng khi có xe mới xuất hiện. Đây là nền tảng cho counting — mỗi xe (1 track_id) chỉ đếm 1 lần.
"""),

    # ============ 5. COUNTER CLASS ============
    md("""
---
## Phần 5 — Implement Counter class từ đầu

Đây là phần **cốt lõi nhất**. Logic:

1. Với mỗi frame, tính **tâm bounding box** của mỗi xe: `(cx, cy) = ((x1+x2)/2, (y1+y2)/2)`
2. Lưu tâm frame trước: `prev_center[track_id] = (cx, cy)`
3. Nếu segment `prev curr` **cắt qua counting line** xe đã đi qua line tăng counter
4. Đánh dấu `(line_name, track_id)` vào set để **không đếm trùng**

Kèm theo: xác định **hướng đi** (ltr/rtl) bằng cross-product.
"""),
    code("""
def segments_cross(a1, a2, b1, b2):
    '''
    Kiểm tra 2 đoạn thẳng a1-a2 và b1-b2 có cắt nhau không.
    Thuật toán CCW (Counter-Clockwise) — chuẩn của computational geometry.

    Ý tưởng: 2 segment cắt nhau khi và chỉ khi các điểm của segment này nằm
    ở 2 phía khác nhau của segment kia (và ngược lại).
    '''
    def ccw(p, q, r):
        # Trả True nếu 3 điểm p,q,r xoay ngược chiều kim đồng hồ
        return (r[1] - p[1]) * (q[0] - p[0]) > (q[1] - p[1]) * (r[0] - p[0])
    return (ccw(a1, b1, b2) != ccw(a2, b1, b2)
            and ccw(a1, a2, b1) != ccw(a1, a2, b2))


def crossing_direction(prev, curr, line_p1, line_p2):
    '''
    Xác định hướng qua line dựa trên dấu cross-product:
    - line_vector = p2 - p1
    - movement_vector = curr - prev
    - cross = vx*my - vy*mx
    - cross > 0: xe đi 'ltr' (theo chiều tay phải của vector line)
    - cross < 0: xe đi 'rtl'
    '''
    vx = line_p2[0] - line_p1[0]
    vy = line_p2[1] - line_p1[1]
    mx = curr[0] - prev[0]
    my = curr[1] - prev[1]
    cross = vx * my - vy * mx
    return "ltr" if cross > 0 else "rtl"


# Test nhanh 2 hàm này
line_p1, line_p2 = (0, 100), (200, 100) # line ngang
prev, curr = (100, 50), (100, 150) # xe đi từ trên xuống
print(f"Xe từ trên xuống, cắt line? {segments_cross(prev, curr, line_p1, line_p2)}")
print(f"Hướng: {crossing_direction(prev, curr, line_p1, line_p2)}")

prev2, curr2 = (100, 150), (100, 50) # xe đi từ dưới lên
print(f"Xe từ dưới lên, cắt line? {segments_cross(prev2, curr2, line_p1, line_p2)}")
print(f"Hướng: {crossing_direction(prev2, curr2, line_p1, line_p2)}")
"""),
    code("""
from collections import defaultdict
from dataclasses import dataclass, field

@dataclass
class Line:
    '''Đại diện 1 counting line.'''
    name: str
    p1: tuple # (x, y)
    p2: tuple # (x, y)
    count_direction: str = "both" # 'both' | 'ltr' | 'rtl'


@dataclass
class Counter:
    lines: list
    # counts[line_name][direction][class_id] = số lượt
    counts: dict = field(default_factory=lambda: defaultdict(
        lambda: defaultdict(lambda: defaultdict(int))))
    # set các (line_name, track_id) đã đếm — chống trùng
    _counted: set = field(default_factory=set)
    # tâm frame trước của mỗi track_id
    _prev_center: dict = field(default_factory=dict)

    def update(self, frame_idx, boxes, ids, classes):
        '''Gọi mỗi frame. Trả về list event vừa đếm trong frame này.'''
        events = []
        for xyxy, tid, cls in zip(boxes, ids, classes):
            if tid is None:
                continue
            tid = int(tid)
            cls = int(cls)
            # Tính tâm box
            cx = (xyxy[0] + xyxy[2]) / 2
            cy = (xyxy[1] + xyxy[3]) / 2
            curr = (cx, cy)

            prev = self._prev_center.get(tid)
            if prev is not None:
                # Với mỗi line, check xem xe có cắt qua không
                for line in self.lines:
                    key = (line.name, tid)
                    if key in self._counted:
                        continue # đã đếm trước đó
                    if not segments_cross(prev, curr, line.p1, line.p2):
                        continue # chưa cắt

                    direction = crossing_direction(prev, curr, line.p1, line.p2)

                    # Filter theo hướng cấu hình
                    if line.count_direction != "both" and line.count_direction != direction:
                        self._counted.add(key) # đánh dấu để không xét lại
                        continue

                    # ĐẾM
                    self.counts[line.name][direction][cls] += 1
                    self._counted.add(key)
                    events.append({
                        "frame": frame_idx,
                        "line": line.name,
                        "direction": direction,
                        "track_id": tid,
                        "class_id": cls,
                    })
            # Cập nhật tâm mới
            self._prev_center[tid] = curr
        return events


# Test nhanh Counter với data giả
lines = [Line(name="mid", p1=(0, 100), p2=(200, 100), count_direction="both")]
counter = Counter(lines=lines)

# Frame 0: xe id=1 ở (100, 50), id=2 ở (100, 150)
counter.update(0, [[95, 45, 105, 55]], [1], [0])
counter.update(0, [[95, 145, 105, 155]], [2], [0])

# Frame 1: id=1 xuống (100, 150) cắt line ltr
# id=2 lên (100, 50) cắt line rtl
ev1 = counter.update(1, [[95, 145, 105, 155]], [1], [0])
ev2 = counter.update(1, [[95, 45, 105, 55]], [2], [0])
print(f"Events id=1: {ev1}")
print(f"Events id=2: {ev2}")
print(f"Counts: {dict(counter.counts)}")
"""),

    # ============ 6. MAIN LOOP ============
    md("""
---
## Phần 6 — Vòng lặp chính: detect + track + count toàn video

Ghép 3 module lại: mỗi frame track cập nhật counter thu thập events.
"""),
    code("""
# Định nghĩa line đếm cho video demo (1764x948)
LINES = [
    Line(name="middle", p1=(100, 474), p2=(1664, 474), count_direction="both"),
]

# Reset model để tracker state sạch
model = YOLO(str(MODEL_PATH))
counter = Counter(lines=LINES)

all_events = []
class_names = None

# Ultralytics có stream mode — memory-efficient
for frame_idx, res in enumerate(model.track(
        source=str(VIDEO_PATH),
        tracker="bytetrack.yaml",
        conf=0.3, iou=0.5, imgsz=512, half=True,
        stream=True, persist=True, verbose=False,
)):
    if class_names is None:
        class_names = res.names

    if res.boxes.id is None:
        continue

    boxes = res.boxes.xyxy.cpu().numpy()
    ids = res.boxes.id.cpu().numpy()
    classes = res.boxes.cls.cpu().numpy()

    # Cập nhật counter nhận events nếu có xe qua line
    frame_events = counter.update(frame_idx, boxes, ids, classes)

    # Thêm timestamp + tên class vào events
    for ev in frame_events:
        ev["time_sec"] = round(frame_idx / FPS, 3)
        ev["class_name"] = class_names[ev["class_id"]]
        all_events.append(ev)

print(f"Tổng events: {len(all_events)}")
print(f"\\nCounts theo line/direction/class:")
for line_name, dirs in counter.counts.items():
    for direction, cls_counts in dirs.items():
        for cls_id, cnt in cls_counts.items():
            print(f" {line_name} - {direction} - {class_names[cls_id]}: {cnt}")
"""),

    # ============ 7. WRITE OUTPUT VIDEO ============
    md("""
---
## Phần 7 — Ghi video output có overlay counter

Chạy lại pipeline nhưng lần này vẽ overlay (boxes + line + counter) và ghi ra file MP4.
"""),
    code("""
OUT_VIDEO = PROJECT_ROOT / "results/videos/notebook_learn_out.mp4"
OUT_VIDEO.parent.mkdir(parents=True, exist_ok=True)

# Ghi video (dùng codec mp4v)
writer = cv2.VideoWriter(str(OUT_VIDEO),
                         cv2.VideoWriter_fourcc(*"mp4v"),
                         FPS, (W, H))

model = YOLO(str(MODEL_PATH))
counter = Counter(lines=LINES)
class_names = None

for frame_idx, res in enumerate(model.track(
        source=str(VIDEO_PATH), tracker="bytetrack.yaml",
        conf=0.3, iou=0.5, imgsz=512, half=True,
        stream=True, persist=True, verbose=False,
)):
    if class_names is None:
        class_names = res.names
    frame_out = res.orig_img.copy()

    if res.boxes.id is not None:
        boxes = res.boxes.xyxy.cpu().numpy()
        ids = res.boxes.id.cpu().numpy()
        classes = res.boxes.cls.cpu().numpy()
        counter.update(frame_idx, boxes, ids, classes)

        # Vẽ box + label
        for box, tid, cls in zip(boxes, ids, classes):
            x1, y1, x2, y2 = box.astype(int)
            cv2.rectangle(frame_out, (x1, y1), (x2, y2), (0, 255, 0), 2)
            label = f"{class_names[int(cls)]}#{int(tid)}"
            cv2.putText(frame_out, label, (x1, max(0, y1 - 6)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

    # Vẽ line
    for line in LINES:
        cv2.line(frame_out, line.p1, line.p2, (0, 0, 255), 2)
        cv2.putText(frame_out, line.name, line.p1,
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

    # Vẽ counter tổng
    y = 30
    for line_name, dirs in counter.counts.items():
        total = sum(sum(c.values()) for c in dirs.values())
        cv2.putText(frame_out, f"{line_name}: {total}", (10, y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        y += 25

    writer.write(frame_out)

writer.release()
print(f"[] Video output: {OUT_VIDEO}")
print(f" Size: {OUT_VIDEO.stat().st_size / 1024:.1f} KB")
"""),
    code("""
# Xem video output
from IPython.display import Video
Video(str(OUT_VIDEO), embed=True, width=800)
"""),

    # ============ 8. AGGREGATE STATS ============
    md("""
---
## Phần 8 — Aggregate statistics với pandas (inline)

Chuyển events list DataFrame group theo nhiều chiều.

**Không dùng `from src.stats.aggregator`** — implement inline.
"""),
    code("""
# Tạo DataFrame từ events
df = pd.DataFrame(all_events)
print(f"Shape: {df.shape}")
print(df.head(10))
"""),
    code("""
# 1) Tổng số theo class
per_class = df["class_name"].value_counts()
print("Số lượt theo class:")
print(per_class)

# 2) Tổng số theo direction
per_direction = df["direction"].value_counts()
print("\\nSố lượt theo direction:")
print(per_direction)

# 3) Tổng theo class × direction
class_dir = df.groupby(["class_name", "direction"]).size().unstack(fill_value=0)
print("\\nBảng class × direction:")
print(class_dir)
"""),
    code("""
# 4) Bucket theo bucket_sec giây
def counts_per_bucket(df, bucket_sec):
    d = df.copy()
    d["bucket"] = (d["time_sec"] // bucket_sec).astype(int)
    return d.groupby(["bucket", "class_name"]).size().unstack(fill_value=0)

per_bucket_1s = counts_per_bucket(df, 1) # mỗi 1 giây
print("Số lượt theo bucket 1 giây:")
print(per_bucket_1s)
"""),
    code("""
# 5) Flow rate: xe/phút, xe/giờ
def flow_rate(df, unit="minute"):
    duration = df["time_sec"].max() - df["time_sec"].min()
    duration = max(duration, 1e-6) # tránh chia 0
    factor = 60.0 if unit == "minute" else 3600.0
    scale = factor / duration
    return {
        "total": round(len(df) * scale, 2),
        "per_class": {c: round(v * scale, 2)
                      for c, v in df["class_name"].value_counts().items()},
    }

fr_min = flow_rate(df, "minute")
fr_hour = flow_rate(df, "hour")
print(f"Xe/phút: {fr_min['total']} Xe/giờ: {fr_hour['total']}")
print(f"Per class (xe/giờ): {fr_hour['per_class']}")
"""),
    code("""
# 6) Cumulative theo thời gian
def cumulative_counts(df):
    d = df.sort_values("time_sec")
    onehot = pd.get_dummies(d["class_name"])
    onehot.index = d["time_sec"].values
    return onehot.cumsum()

cum = cumulative_counts(df)
print(cum.head())
"""),

    # ============ 9. VISUALIZATION ============
    md("""
---
## Phần 9 — Vẽ biểu đồ matplotlib inline
"""),
    code("""
# Chart 1: Bar chart theo class
fig, ax = plt.subplots(figsize=(8, 4))
ax.bar(per_class.index, per_class.values, color="steelblue")
for i, v in enumerate(per_class.values):
    ax.text(i, v, str(v), ha="center", va="bottom", fontsize=11)
ax.set_ylabel("Số lượt qua line")
ax.set_title("Số lượng phương tiện theo loại")
ax.grid(True, alpha=0.3, axis="y")
plt.tight_layout()
plt.show()
"""),
    code("""
# Chart 2: Cumulative line
fig, ax = plt.subplots(figsize=(10, 4))
cum.plot(ax=ax, linewidth=2)
ax.set_xlabel("Thời gian (giây)")
ax.set_ylabel("Số lượt tích luỹ")
ax.set_title("Đếm tích luỹ theo thời gian")
ax.grid(True, alpha=0.3)
ax.legend(title="Loại xe")
plt.tight_layout()
plt.show()
"""),
    code("""
# Chart 3: Stacked bar theo bucket 1 giây
if len(per_bucket_1s) > 0:
    fig, ax = plt.subplots(figsize=(10, 4))
    per_bucket_1s.plot(kind="bar", stacked=True, ax=ax, colormap="tab10")
    ax.set_xlabel("Bucket (giây)")
    ax.set_ylabel("Số lượt")
    ax.set_title("Lưu lượng theo bucket 1 giây (stacked)")
    ax.legend(title="Loại xe")
    plt.xticks(rotation=0)
    plt.tight_layout()
    plt.show()
"""),
    code("""
# Chart 4: Class × Direction
if not class_dir.empty:
    fig, ax = plt.subplots(figsize=(8, 4))
    class_dir.plot(kind="bar", ax=ax, color=["#2ca02c", "#d62728"])
    ax.set_ylabel("Số lượt")
    ax.set_title("Lưu lượng theo loại xe × chiều đi")
    plt.xticks(rotation=0)
    plt.tight_layout()
    plt.show()
"""),

    # ============ 10. EVALUATION ============
    md("""
---
## Phần 10 — Evaluation: so với ground truth

Implement 3 metric chính inline: **Accuracy**, **MAE**, **MAPE**.
"""),
    code("""
def counting_accuracy(pred, gt):
    '''Accuracy = 1 - |pred - gt| / max(gt, 1), clip [0, 1].'''
    if gt == 0:
        return 1.0 if pred == 0 else 0.0
    return max(0.0, 1.0 - abs(pred - gt) / gt)


def mae(preds, gts):
    '''Mean Absolute Error.'''
    assert len(preds) == len(gts) and len(preds) > 0
    return sum(abs(p - g) for p, g in zip(preds, gts)) / len(preds)


def mape(preds, gts):
    '''Mean Absolute Percentage Error — bỏ mẫu gt=0.'''
    pairs = [(p, g) for p, g in zip(preds, gts) if g > 0]
    if not pairs:
        return 0.0
    return 100.0 * sum(abs(p - g) / g for p, g in pairs) / len(pairs)


# Test 3 hàm này
preds = [85, 0, 0, 1] # motorcycle, car, bus, truck (từ pipeline)
gts = [0, 80, 1, 6] # ground truth
print(f"MAE = {mae(preds, gts):.2f}")
print(f"MAPE = {mape(preds, gts):.1f}%")
print(f"Acc per-class: {[counting_accuracy(p, g) for p, g in zip(preds, gts)]}")
"""),
    code("""
# Load GT thực từ file JSON của demo_traffic
import json
with open(PROJECT_ROOT / "data/test_videos/ground_truth/demo_traffic.json") as f:
    gt_data = json.load(f)

gt_counts = {k: v for k, v in gt_data["counts_by_class"].items() if v > 0}
pred_counts = df["class_name"].value_counts().to_dict()

print(f"Ground truth: {gt_counts}")
print(f"Prediction: {pred_counts}")

# So sánh per-class
all_classes = sorted(set(gt_counts) | set(pred_counts))
print(f"\\n{'Class':<15} {'Pred':>6} {'GT':>6} {'|Err|':>6} {'Acc':>7}")
print("-" * 43)
p_list, g_list = [], []
for c in all_classes:
    p = pred_counts.get(c, 0)
    g = gt_counts.get(c, 0)
    acc = counting_accuracy(p, g)
    print(f"{c:<15} {p:>6} {g:>6} {abs(p-g):>6} {acc:>7.3f}")
    p_list.append(p)
    g_list.append(g)

print(f"\\nMAE = {mae(p_list, g_list):.2f}")
print(f"MAPE = {mape(p_list, g_list):.1f}%")
print(f"Overall accuracy (tổng) = {counting_accuracy(sum(p_list), sum(g_list)):.3f}")
"""),

    # ============ SUMMARY ============
    md("""
---
## Tổng kết

Notebook đã đi qua **toàn bộ pipeline detect + track + count + eval**, viết inline mọi thứ:

| Phần | Kỹ thuật | Code chính |
|---|---|---|
| Detection | YOLOv8s | `model.predict()` boxes + cls + conf |
| Tracking | ByteTrack | `model.track(persist=True)` thêm `id` |
| Counting | Segment intersection + cross-product | `Counter.update()` với set chống trùng |
| Direction | Cross-product line × movement | `crossing_direction()` |
| Aggregate | pandas groupby | `df.groupby(["class_name","direction"])` |
| Charts | matplotlib | bar/stacked/cumulative |
| Metrics | Accuracy/MAE/MAPE | Công thức đơn giản |

**Sau khi hiểu notebook này, các bạn có thể**:
- Đọc code trong `src/` mà không thấy bỡ ngỡ — các function trong đó chỉ là refactor gọn hơn
- Custom pipeline: đổi line, đổi model, đổi ngưỡng conf/iou để thử nghiệm
- Debug: nếu counter đếm sai, biết chỗ nào để in prev/curr/cross-product ra kiểm tra

**Tiếp theo**: mở `notebooks/demo_full_pipeline.ipynb` để xem version dùng import (gọn hơn, cho lần chạy thật).
"""),
]


def main():
    nb = {
        "cells": CELLS,
        "metadata": {
            "kernelspec": {"display_name": "Python 3 (yolov8_ft)",
                           "language": "python", "name": "python3"},
            "language_info": {"codemirror_mode": {"name": "ipython", "version": 3},
                              "file_extension": ".py", "mimetype": "text/x-python",
                              "name": "python", "nbconvert_exporter": "python",
                              "pygments_lexer": "ipython3", "version": "3.10.20"},
        },
        "nbformat": 4, "nbformat_minor": 5,
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(nb, f, indent=1, ensure_ascii=False)

    # Normalize để add cell IDs
    import nbformat
    nb2 = nbformat.read(str(OUT), as_version=4)
    nbformat.validator.normalize(nb2)
    nbformat.write(nb2, str(OUT))

    print(f"[] Đã sinh: {OUT}")
    print(f" Số cell: {len(CELLS)}")
    print(f" Kích thước: {OUT.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    main()
