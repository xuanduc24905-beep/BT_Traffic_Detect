"""Sinh notebooks/MASTER_full_project.ipynb — notebook toàn dự án.

Full project trong 1 notebook, từ dataset train eval deploy:
1. Giới thiệu project + topic
2. Khám phá dataset (UA-DETRAC + VN Cần Thơ)
3. Merge dataset + class mapping (chạy được)
4. Training YOLOv8s (có code, có option skip vì mất 5h)
5. Phân tích training results (đọc results.csv, vẽ loss + mAP curves)
6. Confusion matrix + per-class analysis
7. Load model đã train + detect ảnh mẫu
8. Tracking (ByteTrack) hiểu track_id
9. Counter class inline (thuật toán)
10. Full pipeline trên video + xuất video annotated
11. Aggregate + visualize (5 loại chart)
12. Evaluation 2 tầng: mAP + counting vs baseline
13. Streamlit UI (giới thiệu + screenshot)
14. Kết luận + hướng phát triển

Chạy: python scripts/gen_master_notebook.py
"""
import json
from pathlib import Path

OUT = Path("notebooks/MASTER_full_project.ipynb")
OUT.parent.mkdir(parents=True, exist_ok=True)


def md(text):
    return {"cell_type": "markdown", "metadata": {},
            "source": text.strip().splitlines(keepends=True)}


def code(src):
    return {"cell_type": "code", "execution_count": None, "metadata": {},
            "outputs": [], "source": src.strip().splitlines(keepends=True)}


CELLS = []

# ============================================================
# HEADER
# ============================================================
CELLS.append(md("""
# MASTER Notebook — Toàn Dự Án Đếm Xe Giao Thông Việt Nam

**Chủ đề 10 — Bài tập lớn Computer Vision**

> Notebook toàn tập từ chuẩn bị dataset training evaluation deploy.
> Đọc từ trên xuống dưới sẽ hiểu **toàn bộ dự án**. Có thể chạy từng cell hoặc chạy hết.

---

### Mục lục

| # | Phần | Mất bao lâu | Chạy được? |
|---|---|---|---|
| 0 | Setup môi trường | 30 giây | |
| 1 | Khám phá dataset (UA-DETRAC + VN Cần Thơ) | 1 phút | |
| 2 | Merge dataset + class mapping | 2-3 phút | (đã có sẵn `data/merged/`) |
| 3 | Training YOLOv8s (có code + option skip) | ~5 giờ 30 phút | Skip (dùng weight đã train) |
| 4 | Phân tích training results (loss + mAP curves) | 5 giây | (đọc `results.csv`) |
| 5 | Confusion matrix + per-class breakdown | 5 giây | |
| 6 | Load model detect 1 ảnh mẫu | 5 giây | |
| 7 | Tracking với ByteTrack | 15 giây | |
| 8 | Counter class inline + thuật toán | 5 giây | |
| 9 | Pipeline đầy đủ + xuất video annotated | 15-30 giây | |
| 10 | Aggregate + 5 loại chart | 5 giây | |
| 11 | Evaluation 2 tầng vs baseline | 30 giây | |
| 12 | Streamlit UI (giới thiệu) | 0 | Đọc |
| 13 | Kết luận + hướng phát triển | 0 | Đọc |

### Kết quả tóm tắt

- **Model**: YOLOv8s (11M params), 4 class {motorcycle, car, bus, truck}
- **Dataset merged**: 68,547 train / 14,344 val / 56,381 test ảnh
- **Training**: 50 epochs, 5h 30 phút trên RTX 3500 Ada
- **mAP@0.5 tổng**: **0.843** trên test set 56k ảnh
- **mAP motorcycle**: **0.871** (thành công nhờ dataset VN)
"""))

# ============================================================
# 0. SETUP
# ============================================================
CELLS.append(md("""
---
## 0. Setup môi trường
"""))
CELLS.append(code("""
from pathlib import Path
import sys, os, json, shutil, time
from collections import Counter, defaultdict
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from IPython.display import Image, Video, display

import cv2
import torch
import ultralytics
from ultralytics import YOLO

PROJECT_ROOT = Path.cwd()
if PROJECT_ROOT.name == "notebooks":
    PROJECT_ROOT = PROJECT_ROOT.parent
sys.path.insert(0, str(PROJECT_ROOT))

print(f"PyTorch : {torch.__version__}")
print(f"CUDA : {torch.cuda.is_available()} — {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'N/A'}")
print(f"Ultralytics : {ultralytics.__version__}")
print(f"OpenCV : {cv2.__version__}")
print(f"Project root: {PROJECT_ROOT}")
"""))

# ============================================================
# 1. DATASET EXPLORATION
# ============================================================
CELLS.append(md("""
---
## 1. Khám phá dataset

Dự án dùng **2 nguồn dataset**:

| Nguồn | Số ảnh | Class gốc | Đặc điểm |
|---|---|---|---|
| **UA-DETRAC** | 68k / 14k / 56k | car, bus, van, others | Highway TQ, ảnh nhiều nhưng thiếu xe máy |
| **Vietnam Cần Thơ (Roboflow v19)** | 674 / 216 / 214 | bus, car, motorbike, truck | Đường phố VN — **có xe máy** |

Sau khi merge và chuẩn hoá schema, ta có schema thống nhất 4-class: `{0: motorcycle, 1: car, 2: bus, 3: truck}`.
"""))
CELLS.append(code("""
# Đọc data.yaml
import yaml
with open(PROJECT_ROOT / "data/data.yaml") as f:
    cfg = yaml.safe_load(f)
print("data.yaml:")
for k, v in cfg.items():
    print(f" {k}: {v}")
"""))
CELLS.append(code("""
# Kiểm class distribution trong merged dataset
def class_dist(label_dir):
    c = Counter()
    for lbl in Path(label_dir).glob("*.txt"):
        with open(lbl) as f:
            for line in f:
                parts = line.strip().split()
                if parts:
                    c[int(parts[0])] += 1
    return c

names = ["motorcycle", "car", "bus", "truck"]
splits = {}
for split in ["train", "val", "test"]:
    lbl_dir = PROJECT_ROOT / f"data/merged/labels/{split}"
    if lbl_dir.exists():
        splits[split] = class_dist(lbl_dir)

# In bảng
print(f"{'Class':<12}", end="")
for split in splits:
    print(f"{split:>10}", end="")
print()
print("-" * 44)
for i, name in enumerate(names):
    print(f"{name:<12}", end="")
    for split, dist in splits.items():
        print(f"{dist.get(i, 0):>10,}", end="")
    print()
"""))
CELLS.append(code("""
# Visualize class distribution
if splits:
    fig, ax = plt.subplots(figsize=(10, 4))
    x = np.arange(len(names))
    w = 0.28
    colors = ["steelblue", "orange", "green"]
    for i, (split, dist) in enumerate(splits.items()):
        vals = [dist.get(j, 0) for j in range(len(names))]
        ax.bar(x + (i-1)*w, vals, w, label=split, color=colors[i])
    ax.set_xticks(x)
    ax.set_xticklabels(names)
    ax.set_yscale("log")
    ax.set_ylabel("Số instances (log scale)")
    ax.set_title("Class distribution trong merged dataset")
    ax.legend()
    ax.grid(True, alpha=0.3, axis="y")
    plt.tight_layout()
    plt.show()
"""))
CELLS.append(md("""
**Nhận xét**: class `car` chiếm ~84% (imbalance nặng), `motorcycle` chỉ 0.4% — nhưng nhờ chất lượng annotation VN cao, model vẫn đạt mAP motorcycle = 0.87 sau training.
"""))

# ============================================================
# 2. MERGE DATASET
# ============================================================
CELLS.append(md("""
---
## 2. Merge dataset + class mapping

Hai dataset gốc có schema khác nhau. Ta cần **remap** class IDs của cả 2 về schema canonical 4-class.

### Class mapping

```
Canonical: {0: motorcycle, 1: car, 2: bus, 3: truck}

UA-DETRAC (car/bus/van/others) canonical:
  0 car 1 car
  1 bus 2 bus
  2 van 3 truck van gộp vào truck (hình dáng gần nhất)
  3 others BỎ (không có ý nghĩa cho topic)

VN Cần Thơ (bus/car/motorbike/truck) canonical:
  0 bus 2 bus
  1 car 1 car
  2 motorbike 0 motorcycle giá trị chính từ VN
  3 truck 3 truck
```

### Import scripts đã có sẵn:
- `scripts/import_ua_detrac.py` — remap UA-DETRAC (dùng symlink, không copy 60GB)
- `scripts/import_cantho_vn.py` — remap VN Cần Thơ

**Nếu muốn merge lại từ đầu** (cell dưới, chỉ chạy nếu chưa có `data/merged/`):
"""))
CELLS.append(code("""
# Kiểm tra đã merge chưa
merged_exists = (PROJECT_ROOT / "data/merged/labels/train").exists()
print(f"data/merged/ đã có: {merged_exists}")

if not merged_exists:
    print("Chạy merge...")
    os.system(f"cd {PROJECT_ROOT} && python scripts/import_ua_detrac.py")
    os.system(f"cd {PROJECT_ROOT} && python scripts/import_cantho_vn.py")
else:
    print(" Skip merge (đã tồn tại).")
"""))
CELLS.append(code("""
# Xem 1 sample từ mỗi dataset để so
train_imgs = list((PROJECT_ROOT / "data/merged/images/train").glob("detrac_*.jpg"))[:1]
cantho_imgs = list((PROJECT_ROOT / "data/merged/images/train").glob("cantho_*.jpg"))[:1]

fig, axes = plt.subplots(1, 2, figsize=(15, 6))
for ax, imgs, title in [(axes[0], train_imgs, "UA-DETRAC (highway TQ)"),
                         (axes[1], cantho_imgs, "VN Cần Thơ (có xe máy)")]:
    if imgs:
        img = cv2.imread(str(imgs[0]))
        ax.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        ax.set_title(f"{title}\\n{imgs[0].name}")
    ax.axis("off")
plt.tight_layout()
plt.show()
"""))

# ============================================================
# 3. TRAINING (mostly documentation, code with skip)
# ============================================================
CELLS.append(md("""
---
## 3. Training YOLOv8s (⏱ ~5h 30 phút — skip nếu đã có weight)

Cấu hình training cuối cùng của nhóm:

| Hyperparameter | Giá trị | Lý do |
|---|---|---|
| Model | YOLOv8s (11M params) | Cân bằng speed/accuracy |
| Pretrained | yolov8s.pt (COCO) | Warm-start transfer learning |
| Epochs | 50 | Có early-stop patience=15 |
| Batch size | 32 | Vừa VRAM 12GB |
| Image size | 512 | Nhanh hơn 640 ~35% |
| Cache | RAM (~20GB) | Giảm 40% thời gian |
| Optimizer | auto (SGD lr=0.01) | Ultralytics tự chọn |

**Đã có sẵn `weights/v8s_4cls_best.pt`** cell dưới **KHÔNG chạy** mà chỉ giữ code để tham khảo.
"""))
CELLS.append(code('''
# Cell này KHÔNG được chạy — chỉ giữ để tham khảo code training
# Nếu muốn train lại từ đầu, uncomment các dòng dưới:

TRAIN_SCRIPT = """
model = YOLO("yolov8s.pt")
model.train(
    data="data/data.yaml",
    epochs=50,
    imgsz=512,
    batch=32,
    workers=12,
    device=0,
    patience=15,
    cache="ram",
    name="train_v8s_4cls",
    project="runs/detect",
    optimizer="auto",
    seed=42,
    exist_ok=True,
)
"""
print(TRAIN_SCRIPT)
print(" Training sẽ mất ~5h 30 phút.")
print(" Cách chạy nhanh: ./scripts/train.sh fresh (bash script tự chạy nền)")
'''))

# ============================================================
# 4. TRAINING RESULTS
# ============================================================
CELLS.append(md("""
---
## 4. Phân tích training results

Ultralytics tự sinh file `results.csv` chứa loss và metric cho từng epoch, cùng nhiều biểu đồ PNG.
"""))
CELLS.append(code("""
# Đọc results.csv
results_csv = PROJECT_ROOT / "docs/training_report/results.csv"
if not results_csv.exists():
    results_csv = PROJECT_ROOT / "runs/detect/runs/detect/train_v8s_4cls/results.csv"

df_train = pd.read_csv(results_csv)
print(f"Tổng số epoch: {len(df_train)}")
print(f"\\nCác cột: {list(df_train.columns)}")
print(f"\\nEpoch 1 và cuối:")
display(df_train.iloc[[0, -1]][['epoch', 'train/box_loss', 'val/box_loss',
                                 'metrics/mAP50(B)', 'metrics/mAP50-95(B)']])
"""))
CELLS.append(code("""
# Vẽ loss curves + mAP curves
fig, axes = plt.subplots(2, 2, figsize=(14, 8))

# Box loss
ax = axes[0, 0]
ax.plot(df_train['epoch'], df_train['train/box_loss'], label='train', color='steelblue')
ax.plot(df_train['epoch'], df_train['val/box_loss'], label='val', color='orange')
ax.set_title('Box loss theo epoch')
ax.set_xlabel('Epoch'); ax.set_ylabel('Loss')
ax.legend(); ax.grid(True, alpha=0.3)

# Cls loss
ax = axes[0, 1]
ax.plot(df_train['epoch'], df_train['train/cls_loss'], label='train', color='steelblue')
ax.plot(df_train['epoch'], df_train['val/cls_loss'], label='val', color='orange')
ax.set_title('Classification loss')
ax.set_xlabel('Epoch'); ax.set_ylabel('Loss')
ax.legend(); ax.grid(True, alpha=0.3)

# mAP@0.5
ax = axes[1, 0]
ax.plot(df_train['epoch'], df_train['metrics/mAP50(B)'], color='green', linewidth=2)
ax.set_title('mAP@0.5 trên val set')
ax.set_xlabel('Epoch'); ax.set_ylabel('mAP@0.5')
ax.grid(True, alpha=0.3)
ax.axhline(df_train['metrics/mAP50(B)'].max(), color='red', linestyle='--',
           alpha=0.5, label=f"Best={df_train['metrics/mAP50(B)'].max():.3f}")
ax.legend()

# mAP@0.5-0.95
ax = axes[1, 1]
ax.plot(df_train['epoch'], df_train['metrics/mAP50-95(B)'], color='purple', linewidth=2)
ax.set_title('mAP@0.5-0.95 (metric khó hơn)')
ax.set_xlabel('Epoch'); ax.set_ylabel('mAP')
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.show()
"""))
CELLS.append(code("""
# Tìm best epoch theo fitness = 0.1*mAP50 + 0.9*mAP50-95
df_train['fitness'] = 0.1 * df_train['metrics/mAP50(B)'] + 0.9 * df_train['metrics/mAP50-95(B)']
best_idx = df_train['fitness'].idxmax()
best = df_train.iloc[best_idx]

print(f" BEST epoch: {int(best['epoch'])}")
print(f" mAP@0.5 = {best['metrics/mAP50(B)']:.4f}")
print(f" mAP@0.5-0.95 = {best['metrics/mAP50-95(B)']:.4f}")
print(f" Precision = {best['metrics/precision(B)']:.4f}")
print(f" Recall = {best['metrics/recall(B)']:.4f}")
print(f" Fitness = {best['fitness']:.4f}")
"""))

# ============================================================
# 5. CONFUSION MATRIX
# ============================================================
CELLS.append(md("""
---
## 5. Confusion matrix + per-class analysis

Ultralytics cũng tự sinh confusion matrix normalized để xem class nào bị nhầm lẫn nhiều nhất.
"""))
CELLS.append(code("""
# Hiển thị confusion matrix normalized
cm_path = PROJECT_ROOT / "docs/training_report/confusion_matrix_normalized.png"
if not cm_path.exists():
    cm_path = PROJECT_ROOT / "runs/detect/runs/detect/train_v8s_4cls/confusion_matrix_normalized.png"

if cm_path.exists():
    display(Image(str(cm_path), width=700))
else:
    print(f"Không tìm thấy: {cm_path}")
"""))
CELLS.append(code("""
# Hiển thị PR curve per class
pr_path = PROJECT_ROOT / "docs/training_report/BoxPR_curve.png"
if not pr_path.exists():
    pr_path = PROJECT_ROOT / "runs/detect/runs/detect/train_v8s_4cls/BoxPR_curve.png"
if pr_path.exists():
    display(Image(str(pr_path), width=700))
"""))
CELLS.append(md("""
### Kết quả per-class trên test set 56k ảnh

| Class | mAP@0.5 | mAP@0.5-0.95 | Nhận xét |
|---|---|---|---|
| motorcycle | **0.871** | 0.571 | Xuất sắc — nhờ data VN chất lượng cao |
| car | 0.744 | 0.555 | Tốt — data car lớn (418k instances) |
| bus | 0.781 | 0.578 | Tốt — bus dễ detect vì kích thước lớn |
| truck | 0.524 | 0.407 | Yếu — vì trộn 'van' UA-DETRAC vào 'truck' gây confusion |
"""))

# ============================================================
# 6. LOAD MODEL + DETECT
# ============================================================
CELLS.append(md("""
---
## 6. Load model đã train + detect 1 ảnh mẫu
"""))
CELLS.append(code("""
MODEL_PATH = PROJECT_ROOT / "weights/v8s_4cls_best.pt"
BASELINE_PATH = PROJECT_ROOT / "weights/baseline_detrac4.pt"
VIDEO_PATH = PROJECT_ROOT / "data/test_videos/raw/demo_traffic.mp4"

model = YOLO(str(MODEL_PATH))
print(f"Model: {MODEL_PATH.name}")
print(f" Params: {sum(p.numel() for p in model.model.parameters()):,}")
print(f" Classes: {model.names}")
"""))
CELLS.append(code("""
# Detect frame đầu tiên
cap = cv2.VideoCapture(str(VIDEO_PATH))
ret, frame = cap.read()
FPS = cap.get(cv2.CAP_PROP_FPS)
W = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
H = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
N_FRAMES = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
cap.release()
print(f"Video: {W}×{H} @ {FPS} fps, {N_FRAMES} frames")

results = model.predict(frame, conf=0.3, verbose=False)[0]
print(f"\\nDetections: {len(results.boxes)}")
print(f"Classes có mặt: {sorted(set(model.names[int(c)] for c in results.boxes.cls))}")

# Visualize
annotated = results.plot()
fig, ax = plt.subplots(figsize=(14, 8))
ax.imshow(cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB))
ax.set_title(f"Frame 0 — {len(results.boxes)} bounding boxes")
ax.axis("off")
plt.tight_layout()
plt.show()
"""))

# ============================================================
# 7. TRACKING
# ============================================================
CELLS.append(md("""
---
## 7. Tracking với ByteTrack — hiểu `track_id`

`model.track()` khác `model.predict()` ở chỗ trả thêm `boxes.id` — track ID duy nhất cho mỗi xe, giữ nguyên qua các frame.
"""))
CELLS.append(code("""
# Track 20 frame đầu để xem track_id ổn định thế nào
model_test = YOLO(str(MODEL_PATH))
cap = cv2.VideoCapture(str(VIDEO_PATH))

track_history = []
for i in range(20):
    ret, frame = cap.read()
    if not ret:
        break
    res = model_test.track(frame, tracker="bytetrack.yaml", persist=True,
                           conf=0.3, verbose=False)[0]
    ids = res.boxes.id.cpu().numpy().astype(int).tolist() if res.boxes.id is not None else []
    track_history.append(ids)
cap.release()

print("Track IDs qua từng frame (10 frame đầu):")
for f, ids in enumerate(track_history[:10]):
    print(f" Frame {f:2d}: {ids}")
all_ids = set(i for ids in track_history for i in ids)
print(f"\\nTổng {len(all_ids)} track_id unique trong 20 frame mỗi track_id đại diện 1 chiếc xe.")
"""))

# ============================================================
# 8. COUNTER CLASS
# ============================================================
CELLS.append(md("""
---
## 8. Counter class — thuật toán đếm

**Ý tưởng cốt lõi**:
1. Với mỗi frame, tính tâm bounding box: `(cx, cy) = ((x1+x2)/2, (y1+y2)/2)`
2. Lưu tâm frame trước cho mỗi track_id
3. Nếu segment `prev curr` **cắt qua counting line** xe đi qua line tăng counter
4. Đánh dấu `(line_name, track_id)` vào set để **không đếm trùng**

**Xác định hướng** (ltr/rtl) bằng cross-product:
- `line_vector = p2 - p1`, `movement = curr - prev`
- `cross = line_vec.x × mov_vec.y - line_vec.y × mov_vec.x`
- `cross > 0` 'ltr' (theo chiều tay phải của line), `< 0` 'rtl'
"""))
CELLS.append(code("""
def segments_cross(a1, a2, b1, b2):
    '''True nếu 2 segment a1-a2 và b1-b2 cắt nhau. Thuật toán CCW.'''
    def ccw(p, q, r):
        return (r[1] - p[1]) * (q[0] - p[0]) > (q[1] - p[1]) * (r[0] - p[0])
    return (ccw(a1, b1, b2) != ccw(a2, b1, b2)
            and ccw(a1, a2, b1) != ccw(a1, a2, b2))


def crossing_direction(prev, curr, line_p1, line_p2):
    '''Cross-product line_vec × movement_vec dấu quyết định ltr/rtl.'''
    vx = line_p2[0] - line_p1[0]
    vy = line_p2[1] - line_p1[1]
    mx = curr[0] - prev[0]
    my = curr[1] - prev[1]
    cross = vx * my - vy * mx
    return "ltr" if cross > 0 else "rtl"


@dataclass
class Line:
    name: str
    p1: tuple
    p2: tuple
    count_direction: str = "both"


@dataclass
class Counter:
    lines: list
    counts: dict = field(default_factory=lambda: defaultdict(
        lambda: defaultdict(lambda: defaultdict(int))))
    _counted: set = field(default_factory=set)
    _prev_center: dict = field(default_factory=dict)

    def update(self, frame_idx, boxes, ids, classes):
        events = []
        for xyxy, tid, cls in zip(boxes, ids, classes):
            if tid is None:
                continue
            tid, cls = int(tid), int(cls)
            cx = (xyxy[0] + xyxy[2]) / 2
            cy = (xyxy[1] + xyxy[3]) / 2
            curr = (cx, cy)
            prev = self._prev_center.get(tid)
            if prev is not None:
                for line in self.lines:
                    key = (line.name, tid)
                    if key in self._counted:
                        continue
                    if not segments_cross(prev, curr, line.p1, line.p2):
                        continue
                    direction = crossing_direction(prev, curr, line.p1, line.p2)
                    if line.count_direction != "both" and line.count_direction != direction:
                        self._counted.add(key)
                        continue
                    self.counts[line.name][direction][cls] += 1
                    self._counted.add(key)
                    events.append({"frame": frame_idx, "line": line.name,
                                   "direction": direction, "track_id": tid,
                                   "class_id": cls})
            self._prev_center[tid] = curr
        return events


# Unit test nhanh
lines_test = [Line(name="test", p1=(0, 100), p2=(200, 100), count_direction="both")]
c = Counter(lines=lines_test)
c.update(0, [[95, 45, 105, 55]], [1], [0]) # id 1 ở trên
ev = c.update(1, [[95, 145, 105, 155]], [1], [0]) # đi xuống cắt line
print(f"Test event: {ev}")
print(f"Test counts: {dict(c.counts['test'])}")
"""))

# ============================================================
# 9. FULL PIPELINE
# ============================================================
CELLS.append(md("""
---
## 9. Full pipeline: detect + track + count + xuất video

Chạy pipeline hoàn chỉnh: input = video, output = video annotated + CSV events.
"""))
CELLS.append(code("""
# Định nghĩa line
LINES = [Line(name="middle", p1=(100, 474), p2=(1664, 474), count_direction="both")]

OUT_VIDEO = PROJECT_ROOT / "results/videos/master_notebook_out.mp4"
OUT_VIDEO.parent.mkdir(parents=True, exist_ok=True)

writer = cv2.VideoWriter(str(OUT_VIDEO), cv2.VideoWriter_fourcc(*"mp4v"),
                         FPS, (W, H))

model_run = YOLO(str(MODEL_PATH))
counter = Counter(lines=LINES)
class_names = None
all_events = []

t0 = time.time()
for frame_idx, res in enumerate(model_run.track(
        source=str(VIDEO_PATH), tracker="bytetrack.yaml",
        conf=0.3, iou=0.5, imgsz=512, half=True,
        stream=True, persist=True, verbose=False)):
    if class_names is None:
        class_names = res.names
    frame_out = res.orig_img.copy()

    if res.boxes.id is not None:
        boxes = res.boxes.xyxy.cpu().numpy()
        ids = res.boxes.id.cpu().numpy()
        classes = res.boxes.cls.cpu().numpy()
        events = counter.update(frame_idx, boxes, ids, classes)
        for ev in events:
            ev["time_sec"] = round(frame_idx / FPS, 3)
            ev["class_name"] = class_names[ev["class_id"]]
            all_events.append(ev)

        # Vẽ box
        for box, tid, cls in zip(boxes, ids, classes):
            x1, y1, x2, y2 = box.astype(int)
            cv2.rectangle(frame_out, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame_out, f"{class_names[int(cls)]}#{int(tid)}",
                        (x1, max(0, y1 - 6)), cv2.FONT_HERSHEY_SIMPLEX,
                        0.5, (0, 255, 0), 1)

    # Vẽ line
    for line in LINES:
        cv2.line(frame_out, line.p1, line.p2, (0, 0, 255), 2)

    # Vẽ counter tổng
    y = 30
    for line_name, dirs in counter.counts.items():
        total = sum(sum(c.values()) for c in dirs.values())
        cv2.putText(frame_out, f"{line_name}: {total}", (10, y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        y += 25

    writer.write(frame_out)
writer.release()
dt = time.time() - t0
print(f"[] Pipeline chạy {dt:.1f}s ({N_FRAMES/dt:.1f} FPS)")
print(f"[] Video: {OUT_VIDEO}")
print(f"[] Tổng events: {len(all_events)}")
"""))
CELLS.append(code("""
# Xem video output (chỉ hoạt động trong Jupyter local)
Video(str(OUT_VIDEO), embed=True, width=800)
"""))

# ============================================================
# 10. STATS + CHARTS
# ============================================================
CELLS.append(md("""
---
## 10. Aggregate stats + 5 loại biểu đồ
"""))
CELLS.append(code("""
df = pd.DataFrame(all_events)
if not df.empty:
    df["time_min"] = (df["time_sec"] // 60).astype(int)
    print(f"Shape: {df.shape}")
    print(df.head())
"""))
CELLS.append(code("""
# Chart 1: Bar chart theo class
per_class = df["class_name"].value_counts()
fig, ax = plt.subplots(figsize=(8, 4))
ax.bar(per_class.index, per_class.values, color="steelblue")
for i, v in enumerate(per_class.values):
    ax.text(i, v, str(v), ha="center", va="bottom", fontsize=11)
ax.set_ylabel("Số lượt qua line")
ax.set_title("(1) Số lượng phương tiện theo loại")
ax.grid(True, alpha=0.3, axis="y")
plt.tight_layout()
plt.show()
"""))
CELLS.append(code("""
# Chart 2: Cumulative theo thời gian
df_sorted = df.sort_values("time_sec")
onehot = pd.get_dummies(df_sorted["class_name"])
onehot.index = df_sorted["time_sec"].values
cum = onehot.cumsum()

fig, ax = plt.subplots(figsize=(10, 4))
cum.plot(ax=ax, linewidth=2)
ax.set_xlabel("Thời gian (giây)")
ax.set_ylabel("Số lượt tích luỹ")
ax.set_title("(2) Đếm tích luỹ theo thời gian")
ax.grid(True, alpha=0.3)
ax.legend(title="Loại xe")
plt.tight_layout()
plt.show()
"""))
CELLS.append(code("""
# Chart 3: Stacked bar theo bucket 1 giây
df_b = df.copy()
df_b["bucket"] = df_b["time_sec"].astype(int)
per_bucket = df_b.groupby(["bucket", "class_name"]).size().unstack(fill_value=0)

fig, ax = plt.subplots(figsize=(10, 4))
per_bucket.plot(kind="bar", stacked=True, ax=ax, colormap="tab10")
ax.set_xlabel("Bucket (giây)")
ax.set_ylabel("Số lượt")
ax.set_title("(3) Lưu lượng theo bucket 1 giây (stacked)")
ax.legend(title="Loại xe")
plt.xticks(rotation=0)
plt.tight_layout()
plt.show()
"""))
CELLS.append(code("""
# Chart 4: Direction breakdown
class_dir = df.groupby(["class_name", "direction"]).size().unstack(fill_value=0)
fig, ax = plt.subplots(figsize=(8, 4))
class_dir.plot(kind="bar", ax=ax, color=["#2ca02c", "#d62728"])
ax.set_ylabel("Số lượt")
ax.set_title("(4) Lưu lượng theo loại xe × chiều đi")
plt.xticks(rotation=0)
plt.tight_layout()
plt.show()
"""))
CELLS.append(code("""
# Chart 5: Heatmap bucket × class
if not per_bucket.empty:
    fig, ax = plt.subplots(figsize=(8, max(3, len(per_bucket) * 0.4)))
    im = ax.imshow(per_bucket.values, aspect="auto", cmap="YlOrRd")
    ax.set_xticks(range(len(per_bucket.columns)))
    ax.set_xticklabels(per_bucket.columns, rotation=30)
    ax.set_yticks(range(len(per_bucket.index)))
    ax.set_yticklabels(per_bucket.index)
    ax.set_xlabel("Loại xe")
    ax.set_ylabel("Bucket (giây)")
    ax.set_title("(5) Heatmap thời gian × class")
    for i in range(len(per_bucket.index)):
        for j in range(len(per_bucket.columns)):
            v = int(per_bucket.values[i, j])
            if v > 0:
                ax.text(j, i, str(v), ha="center", va="center",
                        color="white" if v > per_bucket.values.max()*0.5 else "black",
                        fontsize=9)
    plt.colorbar(im, ax=ax, label="Số lượt")
    plt.tight_layout()
    plt.show()
"""))
CELLS.append(code("""
# Bonus: Flow rate
duration = df["time_sec"].max() - df["time_sec"].min()
if duration > 0:
    xe_per_hour = len(df) * 3600 / duration
    print(f"⏱ Video dài: {duration:.1f} giây")
    print(f" Flow rate: {xe_per_hour:.0f} xe/giờ (extrapolate từ video ngắn)")
    print(f"\\n Per class (xe/giờ):")
    for cls, cnt in per_class.items():
        print(f" {cls:10s}: {cnt * 3600 / duration:.0f}")
"""))

# ============================================================
# 11. EVALUATION VS BASELINE
# ============================================================
CELLS.append(md("""
---
## 11. Evaluation 2 tầng — so với baseline

- **Tầng A**: mAP trên test set 56k ảnh (chuẩn ML)
- **Tầng B**: counting accuracy trên video có GT (chuẩn task)

Baseline: `weights/baseline_detrac4.pt` (YOLOv8n cũ, 3M params, train 3 epoch trên UA-DETRAC 4-class gốc {car/bus/van/others}, không có motorcycle).
"""))
CELLS.append(code("""
# Metric functions inline
def counting_accuracy(pred, gt):
    if gt == 0: return 1.0 if pred == 0 else 0.0
    return max(0.0, 1.0 - abs(pred - gt) / gt)
def mae(preds, gts):
    return sum(abs(p-g) for p,g in zip(preds, gts)) / len(preds)
def mape(preds, gts):
    pairs = [(p,g) for p,g in zip(preds, gts) if g > 0]
    return 100.0 * sum(abs(p-g)/g for p,g in pairs) / len(pairs) if pairs else 0.0


# Load GT
with open(PROJECT_ROOT / "data/test_videos/ground_truth/demo_traffic.json") as f:
    gt = json.load(f)
gt_counts = {k: v for k, v in gt["counts_by_class"].items() if v > 0}
print(f"Ground truth: {gt_counts}")
"""))
CELLS.append(code("""
# Tầng B — chạy baseline_detrac4 để lấy prediction
model_baseline = YOLO(str(BASELINE_PATH))
counter_baseline = Counter(lines=LINES)
class_names_bl = None
events_baseline = []

for frame_idx, res in enumerate(model_baseline.track(
        source=str(VIDEO_PATH), tracker="bytetrack.yaml",
        conf=0.3, iou=0.5, imgsz=512, half=True,
        stream=True, persist=True, verbose=False)):
    if class_names_bl is None:
        class_names_bl = res.names
    if res.boxes.id is None:
        continue
    boxes = res.boxes.xyxy.cpu().numpy()
    ids = res.boxes.id.cpu().numpy()
    classes = res.boxes.cls.cpu().numpy()
    for ev in counter_baseline.update(frame_idx, boxes, ids, classes):
        ev["class_name"] = class_names_bl[ev["class_id"]]
        events_baseline.append(ev)

pred_baseline = pd.DataFrame(events_baseline)["class_name"].value_counts().to_dict() if events_baseline else {}
pred_new = df["class_name"].value_counts().to_dict()

print(f"Baseline pred: {pred_baseline}")
print(f"Model mới pred: {pred_new}")
print(f"GT: {gt_counts}")
"""))
CELLS.append(code("""
# Compute metrics cho cả 2 model
def compute(pred, gt):
    classes = sorted(set(pred) | set(gt))
    p_list = [pred.get(c, 0) for c in classes]
    g_list = [gt.get(c, 0) for c in classes]
    return {
        "MAE": mae(p_list, g_list),
        "MAPE": mape(p_list, g_list),
        "Overall Acc": counting_accuracy(sum(p_list), sum(g_list)),
        "per_class": {c: {"pred": p, "gt": g, "acc": counting_accuracy(p, g)}
                      for c, p, g in zip(classes, p_list, g_list)},
    }

m_baseline = compute(pred_baseline, gt_counts)
m_new = compute(pred_new, gt_counts)

print(f"{'Metric':<15} {'Baseline':>12} {'Model mới':>12}")
print("-" * 41)
print(f"{'Overall Acc':<15} {m_baseline['Overall Acc']:>12.3f} {m_new['Overall Acc']:>12.3f}")
print(f"{'MAE':<15} {m_baseline['MAE']:>12.2f} {m_new['MAE']:>12.2f}")
print(f"{'MAPE (%)':<15} {m_baseline['MAPE']:>12.1f} {m_new['MAPE']:>12.1f}")
"""))
CELLS.append(code("""
# Chart so sánh
labels = ['MAE', 'MAPE (%)', 'Overall Acc']
baseline_vals = [m_baseline['MAE'], m_baseline['MAPE'], m_baseline['Overall Acc'] * 100]
new_vals = [m_new['MAE'], m_new['MAPE'], m_new['Overall Acc'] * 100]

fig, ax = plt.subplots(figsize=(9, 4))
x = np.arange(len(labels))
w = 0.35
ax.bar(x - w/2, baseline_vals, w, label='Baseline (v8n cũ)', color='gray')
ax.bar(x + w/2, new_vals, w, label='Model mới (v8s + VN data)', color='steelblue')
ax.set_xticks(x)
ax.set_xticklabels(labels)
ax.set_title('So sánh counting metrics: baseline vs model mới')
ax.legend()
ax.grid(True, alpha=0.3, axis='y')
for i, v in enumerate(baseline_vals):
    ax.text(i - w/2, v, f'{v:.1f}', ha='center', va='bottom', fontsize=10)
for i, v in enumerate(new_vals):
    ax.text(i + w/2, v, f'{v:.1f}', ha='center', va='bottom', fontsize=10)
plt.tight_layout()
plt.show()
"""))
CELLS.append(md("""
### Kết luận evaluation

- **Detection**: model mới đạt mAP@0.5 = **0.843** trên test set 56k ảnh, baseline chỉ 0.009 (do schema lệch)
- **Counting**: baseline có MAE thấp hơn trên **video demo cụ thể này** vì trùng schema van/others, nhưng KHÔNG detect được xe máy
- **Điểm mạnh nhất của model mới**: **detect xe máy với mAP 0.871** — điều mà baseline không thể làm

Trên video giao thông VN thực tế (có xe máy chiếm 80-90%), model mới sẽ vượt trội hoàn toàn.
"""))

# ============================================================
# 12. STREAMLIT UI
# ============================================================
CELLS.append(md("""
---
## 12. Streamlit UI — Web interface

Ngoài dùng notebook, nhóm còn xây web UI để dùng dễ hơn:

```bash
cd ~/vn_traffic_ai
conda activate yolov8_ft
streamlit run ui/streamlit_app.py
```

**3 tab chính**:
- **Tab 1 (Run)**: upload video chỉnh model/line/threshold/FP16 chạy pipeline xem video output
- **Tab 2 (Stats)**: bucket thời gian, 5 loại chart, flow rate, peak period
- **Tab 3 (Eval)**: upload GT JSON hoặc điền tay tính accuracy/MAE/MAPE per-class

Web UI dùng chính các module trong `src/` — không viết lại pipeline. Cùng model, cùng logic.
"""))

# ============================================================
# 13. CONCLUSION
# ============================================================
CELLS.append(md("""
---
## 13. Kết luận + hướng phát triển

### Đã hoàn thành

Đầy đủ 6 yêu cầu topic 10:
1. Detection: YOLOv8s fine-tune trên 68k ảnh, mAP@0.5 = 0.843
2. Tracking: ByteTrack (built-in Ultralytics), track_id ổn định
3. Counting với multi-line và direction (ltr/rtl)
4. Thống kê theo class + thời gian (bucket 30s 1h) + flow rate + peak period
5. 5 loại biểu đồ: bar, cumulative, stacked, direction, heatmap
6. Evaluation 2 tầng: mAP + counting accuracy vs baseline

### Phần mở rộng

- Merge 2 dataset (UA-DETRAC + VN Cần Thơ) thêm motorcycle cho topic VN
- Direction-aware counting bằng cross-product
- FP16 inference (tăng tốc 1.5-2×)
- Streamlit web UI cho non-developer
- Auto-resume training (dừng bất kỳ lúc nào và tiếp tục)
- Eval 2 tầng chuẩn ML + task-level

### Hạn chế + hướng cải thiện

| Hạn chế | Giải pháp |
|---|---|
| Truck mAP thấp (0.52) do trộn van+truck | Relabel data hoặc dùng 5-class schema |
| Motorcycle chỉ 2k samples (imbalance) | Bổ sung dataset VN đa dạng hơn |
| GT counting chỉ có 1 video 5.9s | Đếm tay thêm video dài |
| Chưa xử lý tình huống mưa/đêm/camera rung | Data augmentation + domain adaptation |

### Hướng phát triển tiếp

- Thử YOLO11, YOLOv10, RT-DETR để so mAP + speed
- Deploy ONNX/TensorRT cho edge device (Jetson Nano, Raspberry Pi)
- Realtime dashboard với alerting (cảnh báo khi lưu lượng vượt ngưỡng)
- Multi-camera fusion để track xe qua nhiều camera

---

**Repo**: https://github.com/xuanduc24905-beep/BT_Traffic_Detect

**Notebook liên quan**:
- `notebooks/demo_full_pipeline.ipynb` — bản gọn (dùng import từ `src/`)
- `notebooks/learn_pipeline_from_scratch.ipynb` — bản full inline
- `notebooks/MASTER_full_project.ipynb` — **file này** (toàn dự án end-to-end)

**Báo cáo Word**:
- `docs/BAO_CAO_CHINH_THUC.docx` — báo cáo nộp GVHD
- `docs/BAO_CAO_KY_THUAT.docx` — tài liệu nội bộ nhóm
"""))


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
