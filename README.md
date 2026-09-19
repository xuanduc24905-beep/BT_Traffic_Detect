# VN Traffic AI — Phát hiện, theo vết và đếm phương tiện giao thông Việt Nam

Hệ thống end-to-end: **video giao thông VN detection tracking counting
thống kê + đánh giá**. Đề tài nhóm 4 người, dùng chung 1 conda env `yolov8_ft`.

## Tech stack

- **Detection**: Ultralytics YOLOv8/v11
- **Tracking**: ByteTrack / BoT-SORT (built-in Ultralytics)
- **Counting**: line/zone crossing, ID-based deduplication
- **Stats & Viz**: pandas + matplotlib
- **Evaluation**: Accuracy, MAE, MAPE trên video test có ground truth

## Cấu trúc thư mục

```
vn_traffic_ai/
├── data/
│ ├── raw/ # dataset gốc (gitignored)
│ │ ├── ua_detrac/
│ │ ├── roboflow_vn/
│ │ └── visdrone_vid/
│ ├── merged/ # sau merge_datasets.py (gitignored)
│ │ ├── images/{train,val,test}/
│ │ └── labels/{train,val,test}/
│ ├── test_videos/ # video VN tự quay cho eval (gitignored)
│ │ ├── raw/
│ │ └── ground_truth/ # JSON đếm thủ công
│ └── data.yaml # config 5 class Ultralytics
├── configs/
│ ├── class_mapping.json # remap từng dataset về 5 class chung
│ └── counting_zones.json # định nghĩa line/zone đếm cho video test
├── weights/
│ └── yolov8n.pt # pretrained COCO
├── src/
│ ├── detection/ # Người 1
│ ├── tracking/ # Người 2
│ ├── stats/ # Người 3
│ ├── evaluation/ # Người 4
│ └── pipeline/ # tích hợp end-to-end
├── scripts/
│ ├── merge_datasets.py # gộp UA-DETRAC + Roboflow VN + VisDrone
│ ├── prepare_test_video.py # cắt frame + template ground truth
│ └── download_datasets.sh
├── notebooks/
├── tests/
├── docs/
│ ├── TEAM_ASSIGNMENT.md # phân công chi tiết + timeline
│ └── DATA_GUIDE.md # hướng dẫn download data
├── results/{figures,tables,videos}/
└── logs/
```

## Setup

```bash
# Dùng lại env sẵn có
conda activate yolov8_ft

# Cài thêm dependencies cho tracking + counting
pip install -r requirements.txt

# Kiểm tra CUDA
python -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0))"
```

## Dataset (5 lớp chung)

```
0: motorcycle
1: car
2: bus
3: truck
4: bicycle
```

Ba nguồn dữ liệu:
1. **UA-DETRAC** — benchmark quốc tế (car/bus/truck).
2. **Roboflow "Vietnamese Traffic Vehicles"** — bổ sung motorcycle, bicycle VN.
3. **VisDrone-VID** — video có tracking ID, dùng cho Person 2 test.

Xem [docs/DATA_GUIDE.md](docs/DATA_GUIDE.md) để download.

## Phân công 4 người

| Người | Module | Deliverable |
|---|---|---|
| 1 | `src/detection/` | Train YOLOv8 trên merged data, xuất `best.pt`, đánh giá mAP |
| 2 | `src/tracking/` | Wrapper ByteTrack/BoT-SORT + line/zone counter chống đếm trùng |
| 3 | `src/stats/` | Aggregate output tracking CSV + biểu đồ theo class × thời gian |
| 4 | `src/evaluation/` | Ground truth thủ công + tính Accuracy/MAE/MAPE + tích hợp toàn hệ thống |

Chi tiết: [docs/TEAM_ASSIGNMENT.md](docs/TEAM_ASSIGNMENT.md).

## Quy trình chạy end-to-end (target)

```bash
# 1. Chuẩn bị data
bash scripts/download_datasets.sh
python scripts/merge_datasets.py

# 2. Train detection (Người 1)
python -m src.detection.train --data data/data.yaml --epochs 50

# 3. Chạy pipeline trên video test (Người 4 tích hợp)
python -m src.pipeline.run \
    --video data/test_videos/raw/nga_tu_01.mp4 \
    --weights runs/detect/train/weights/best.pt \
    --tracker bytetrack \
    --counting-config configs/counting_zones.json \
    --output results/videos/nga_tu_01_out.mp4

# 4. Đánh giá (Người 4)
python -m src.evaluation.compare \
    --pred results/tables/nga_tu_01_counts.csv \
    --gt data/test_videos/ground_truth/nga_tu_01.json
```
