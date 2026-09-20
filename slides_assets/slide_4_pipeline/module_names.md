# Slide 4 — Pipeline 5 module (tên chuẩn theo code nhóm)

Sơ đồ: 5 hộp nối mũi tên theo thứ tự trái → phải.

| Thứ tự | Tên hiển thị trên slide | Thư mục / file trong code | Chức năng ngắn |
|---|---|---|---|
| 1 | **Detection** | `src/detection/` (train.py, infer.py, evaluate.py) | YOLOv8s output bbox + class + confidence |
| 2 | **Tracking** | `src/tracking/track.py` | ByteTrack gán track_id ổn định qua frame |
| 3 | **Counting** | `src/tracking/counter.py` (Line, Counter) | Line crossing + chống đếm trùng bằng set track_id |
| 4 | **Stats** | `src/stats/aggregator.py`, `visualize.py` | Sinh CSV events, biểu đồ per class + per time bucket |
| 5 | **UI** | `ui/streamlit_app.py` | Streamlit dashboard: upload video, chọn model, so sánh 2 pipeline |

Có 1 module "keo dán" nối 5 cái lại: `src/pipeline/run.py` chứa hàm `run_pipeline()`
điều phối luồng: detect → track → count → sinh events + video annotated.

## Gợi ý màu shape (nếu template có sẵn):
- Detection = xanh dương (dữ liệu vào)
- Tracking = cam (xử lý theo thời gian)
- Counting = đỏ (nghiệp vụ chính)
- Stats = xanh lá (kết quả)
- UI = xám (interface người dùng)
