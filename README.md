# VN Traffic AI — Phát hiện, theo vết và đếm phương tiện giao thông Việt Nam

Hệ thống end-to-end: **video giao thông VN → detection → tracking → counting → thống kê + đánh giá**.
Đề tài nhóm, chủ đề 10, dùng chung 1 conda env `yolov8_ft`.

---

## Điểm nổi bật (kết quả mới nhất)

- **2 pipeline so sánh trực tiếp:**
  - **Baseline** — `yolov8s.pt` COCO gốc (80 lớp, filter 4 phương tiện), không huấn luyện.
  - **Improved** — best.pt sau **2 vòng fine-tune** trên dataset Việt Nam.
- **Detection val (14,344 ảnh):** mAP@0.5 = **0.850**, mAP@0.5:0.95 = **0.638**.
  - motorcycle mAP@0.5 = **0.949** (cao nhất 4 class, nhờ boost vnv3).
  - bus 0.911, car 0.848, truck 0.695.
- **Tốc độ:** Improved 72.7 FPS vs Baseline 40.7 FPS (**nhanh hơn 1.79×**).
- **Streamlit dashboard** có 2 chế độ: chạy 1 pipeline hoặc so sánh 2 pipeline side-by-side + video preview H.264 inline.
- **Đánh giá 3 tầng:** Detection (mAP) + Tracking proxy (ID stability) + Counting (MAE/MAPE).

---

## Tech stack

- **Detection:** Ultralytics YOLOv8s (11.2M params, 28.6 GFLOPs, imgsz 512-640)
- **Tracking:** ByteTrack (default) / BoT-SORT — built-in Ultralytics
- **Counting:** line/zone crossing, direction (cross-product), ID-based deduplication
- **Stats & Viz:** pandas + matplotlib
- **UI:** Streamlit dashboard (dual pipeline compare mode)
- **Evaluation:** mAP, Accuracy, MAE, MAPE + tracking proxy (id_stability, overcount_rate)

---

## Cấu trúc thư mục

```
vn_traffic_ai/
├── baseline/
│   └── 10_traffic_counting.py         # code baseline (đã đổi sang v8s cho fair)
├── configs/
│   └── counting_zones.json            # line/zone đếm cho từng video test
├── data/
│   ├── data.yaml                      # schema 4 lớp {motorcycle, car, bus, truck}
│   ├── merged/                        # dataset gộp UA-DETRAC + CanTho + vnv3 (gitignored)
│   └── test_videos/                   # video test + ground truth (gitignored)
├── docs/
│   ├── comparison_report/             # BÁO CÁO SO SÁNH BASELINE vs IMPROVED
│   │   ├── comparison_report.md
│   │   ├── BAO_CAO_BASELINE_VS_IMPROVED.docx
│   │   └── charts/                    # 8 chart PNG dùng cho PPT
│   ├── TEAM_ASSIGNMENT.md
│   └── DATA_GUIDE.md
├── notebooks/
│   └── report_baseline_vs_improved.ipynb  # NOTEBOOK BÁO CÁO CHÍNH (đã embed 9 chart)
├── scripts/
│   ├── import_vnv3.py                 # merge Vietnamese vehicle v3 (remap class)
│   ├── bench_new_video.py             # benchmark detection thô trên video mới
│   ├── eval_counting_2pipelines.py    # eval counting baseline vs improved
│   ├── eval_tracking_proxy.py         # tracking proxy metrics (ID stability)
│   ├── gen_comparison_report.py       # sinh chart + markdown report
│   ├── gen_report_docx.py             # sinh file Word báo cáo
│   ├── gen_report_notebook.py         # sinh notebook báo cáo
│   └── train.sh
├── slides_assets/                     # assets đóng gói cho từng slide PPT
│   ├── slide_3_bai_toan/
│   ├── slide_4_pipeline/
│   ├── slide_5_yolov8_variants/
│   ├── slide_6_data_finetune/
│   └── slide_7_tracking_need/
├── src/
│   ├── detection/                     # Người 1 — train.py, evaluate.py, infer.py
│   ├── tracking/                      # Người 2 — track.py, counter.py
│   ├── stats/                         # Người 3 — aggregator.py, visualize.py
│   ├── evaluation/                    # Người 4 — metrics.py (+ tracking proxy)
│   └── pipeline/                      # tích hợp end-to-end: run.py
├── ui/
│   └── streamlit_app.py               # dashboard 2 mode: single / compare
├── results/
│   ├── tables/                        # events.csv, eval JSON, benchmark
│   ├── figures/                       # biểu đồ auto-sinh
│   └── videos/                        # video output (gitignored, mp4v + H.264)
├── weights/
│   └── yolov8s.pt                     # pretrained COCO (baseline)
├── runs/                              # training outputs (gitignored)
│   └── detect/.../train_v8s_ft_vnv3/weights/best.pt  # ← model tốt nhất
└── logs/
```

---

## Setup

```bash
conda activate yolov8_ft
pip install -r requirements.txt

# Kiểm tra CUDA
python -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0))"

# Cài ffmpeg cho Streamlit H.264 preview (nếu chưa có)
sudo apt install ffmpeg   # Ubuntu/WSL
```

---

## Dataset (schema 4 lớp)

```
0: motorcycle    1: car    2: bus    3: truck
```

**3 nguồn hợp nhất → `data/merged/`:**

| Nguồn | Vai trò | Ảnh |
|---|---|---|
| **UA-DETRAC** (Trung Quốc) | car, bus, truck | ~68k |
| **Vehicle Vietnam-CanTho v19** (Roboflow) | motorcycle chính | 1,235 |
| **Vietnamese vehicle v3** (Roboflow) | boost motorcycle (+2,232 bbox) | 1,547 |
| **Tổng train** | | ~137k ảnh, ~503k bbox |

Val: 14,344 ảnh. Chi tiết download: [docs/DATA_GUIDE.md](docs/DATA_GUIDE.md).

**Class remapping vnv3:** vì Roboflow export với class id khác, script [scripts/import_vnv3.py](scripts/import_vnv3.py) tự động remap `{0:1, 1:0, 2:3, 3:2}` trước khi merge.

---

## Quy trình training (Improved model)

**Vòng 1 — `train_v8s_4cls`:**
```bash
yolo detect train model=yolov8s.pt data=data/data.yaml \
    epochs=50 batch=32 imgsz=512 lr0=0.01 \
    project=runs/detect name=train_v8s_4cls
```
- Init COCO pretrained, reset head 80→4 lớp.
- Thời gian ~5h 30m trên RTX 3500 Ada 12GB.
- Best mAP50 = 0.848 (epoch 6).

**Vòng 2 — `train_v8s_ft_vnv3` (continual):**
```bash
yolo detect train model=runs/.../train_v8s_4cls/weights/best.pt \
    data=data/data.yaml \
    epochs=25 batch=32 imgsz=512 \
    lr0=0.001 lrf=0.01 patience=8 \
    project=runs/detect name=train_v8s_ft_vnv3
```
- Init từ best.pt vòng 1, thêm 1,547 ảnh vnv3.
- **LR 0.001** (thấp 10×) → tránh catastrophic forgetting.
- Early stop ở epoch 18, tổng 2h 20m.
- Best mAP50 = **0.850** (epoch 10).

---

## Quy trình end-to-end

```bash
# 1. Chạy pipeline single model
python -m src.pipeline.run \
    --video data/test_videos/raw/demo_traffic.mp4 \
    --weights runs/detect/.../train_v8s_ft_vnv3/weights/best.pt \
    --tracker bytetrack.yaml \
    --counting-config configs/counting_zones.json \
    --video-key demo_traffic \
    --out-csv results/tables/demo_events.csv \
    --out-video results/videos/demo_out.mp4

# 2. Benchmark counting: baseline vs improved
python scripts/eval_counting_2pipelines.py

# 3. Tracking proxy metrics (ID stability)
PYTHONPATH=. python scripts/eval_tracking_proxy.py

# 4. Sinh báo cáo Markdown + Word + chart
python scripts/gen_comparison_report.py
python scripts/gen_report_docx.py

# 5. Chạy Streamlit dashboard (2 mode: single / compare)
streamlit run ui/streamlit_app.py
```

---

## Đánh giá — 3 tầng

### Tầng 1: Detection (mAP)

Chạy `yolo val` trên val set 14,344 ảnh:

| Class | Precision | Recall | mAP@0.5 | mAP@0.5:0.95 |
|---|---|---|---|---|
| motorcycle | 0.858 | **0.917** | **0.949** ⭐ | 0.609 |
| car | 0.899 | 0.794 | 0.848 | 0.629 |
| bus | 0.917 | 0.819 | 0.911 | 0.772 |
| truck | 0.803 | 0.631 | 0.695 | 0.543 |
| **all** | **0.869** | **0.790** | **0.850** | **0.638** |

### Tầng 2: Counting (task-level)

So sánh trên `demo_traffic.mp4` (5.9s, GT=87 xe):

| Chỉ số | Baseline (COCO) | Improved (fine-tune) |
|---|---|---|
| Total pred | 71 | 104 |
| MAE | 4.0 | 5.25 |
| MAPE (%) | 49.9 | 46.8 |
| Overall accuracy | 81.6% | 80.5% |
| **FPS** | 40.7 | **72.7** (1.79× nhanh) |

### Tầng 3: Tracking proxy (không có GT tracking per-frame)

Metric mới trong [src/evaluation/metrics.py](src/evaluation/metrics.py):
- `track_count` — unique track_id qua line
- `overcount_rate = (pred - gt) / gt`
- `id_stability = 1 - |overcount_rate|` — proxy cho IDF1

| | Track count | Overcount rate | ID stability |
|---|---|---|---|
| Baseline | 71 | **-18.4%** (miss) | 0.816 |
| Improved | 104 | **+19.5%** (ID switch) | 0.805 |

Insight: 2 pipeline có stability tương đương nhưng bị lỗi ở **khía cạnh khác nhau** — baseline miss, improved đếm dư.

**Chưa có IDF1/MOTA/HOTA chuẩn** vì cần GT tracking per-frame (chi phí label quá cao cho scope coursework).

---

## Streamlit dashboard

```bash
streamlit run ui/streamlit_app.py
```

**Tab 1 — Chạy pipeline:**
- Upload video → chọn weights → chỉnh conf/iou/imgsz/line → chạy.
- Video output **preview inline** (auto transcode H.264 bằng ffmpeg).

**Tab 1 — Compare mode:**
- Chọn `⚖ So sánh 2 pipeline` → chọn 2 weights (Baseline + Improved) → chạy 1 phát ra 2 output cạnh nhau.
- Bảng metrics: tổng đếm, runtime, FPS, chênh lệch.
- Bar chart per-class + info box tự sinh đọc kết quả.

**Tab 2 — Thống kê:** biểu đồ per class, per time bucket, cumulative, flow rate.

**Tab 3 — Đánh giá:** upload GT JSON → tính accuracy/MAE/MAPE per class.

---

## File deliverable chính

| Loại | Đường dẫn |
|---|---|
| Báo cáo Markdown | [docs/comparison_report/comparison_report.md](docs/comparison_report/comparison_report.md) |
| Báo cáo Word | [docs/comparison_report/BAO_CAO_BASELINE_VS_IMPROVED.docx](docs/comparison_report/BAO_CAO_BASELINE_VS_IMPROVED.docx) |
| Notebook báo cáo (đã chạy sẵn) | [notebooks/report_baseline_vs_improved.ipynb](notebooks/report_baseline_vs_improved.ipynb) |
| Assets cho PPT | [slides_assets/](slides_assets/) |
| 8 chart PPT | [docs/comparison_report/charts/](docs/comparison_report/charts/) |
| Best weights | `runs/detect/.../train_v8s_ft_vnv3/weights/best.pt` |

---

## Phân công 4 người

| Người | Module | Deliverable |
|---|---|---|
| 1 | `src/detection/` | Train YOLOv8, xuất `best.pt`, đánh giá mAP |
| 2 | `src/tracking/` | ByteTrack wrapper + line/zone counter |
| 3 | `src/stats/` | Aggregate events CSV + biểu đồ per class × thời gian |
| 4 | `src/evaluation/` | Ground truth thủ công + Accuracy/MAE/MAPE + tracking proxy + pipeline integration |

Chi tiết: [docs/TEAM_ASSIGNMENT.md](docs/TEAM_ASSIGNMENT.md).

---

## Hạn chế đã biết & hướng phát triển

**Hạn chế:**
- Motorcycle chỉ 0.85% bbox train → mAP@0.5:0.95 = 0.609 (thấp hơn class khác).
- Truck confusion cao (mAP 0.695) do UA-DETRAC gộp `van → truck`.
- Improved model kém generalize ra video out-of-distribution (recall giảm mạnh khi test video screen recording độ phân giải thấp).
- Chưa đo IDF1/MOTA chuẩn do thiếu GT tracking per-frame.

**Hướng mở rộng:**
- Fine-tune với `freeze=10` (chỉ train head, giữ backbone COCO) → tăng generalization.
- Class-balanced sampling / focal loss.
- Test đa dạng video VN (5-10 phút mỗi video).
- Deploy edge (Jetson) test real-time.

---

## Bài học chính

> "**Same model, better data → better result**" — cùng kiến trúc YOLOv8s (không đổi params), chỉ thay data + training strategy → mAP xe máy tăng lên 0.949.

Nhưng cần cẩn thận: fine-tune sâu trên dataset hẹp có thể làm **mất generalization** khi test out-of-distribution. Đây là trade-off điển hình của specialist vs generalist model.
