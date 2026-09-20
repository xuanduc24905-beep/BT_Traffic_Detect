# Slide 5 — Bảng so sánh YOLOv8 variants

Số liệu chính thức từ Ultralytics (test trên COCO val2017, imgsz=640, RTX 3080/A100).
Highlight cột **s** — bản nhóm dùng.

| Variant | Params (M) | GFLOPs @ 640 | mAP@0.5:0.95 COCO | Speed CPU ONNX (ms) | Speed T4 TensorRT (ms) |
|---|---|---|---|---|---|
| YOLOv8**n** (nano)  | 3.2  | 8.7  | 37.3 | 80.4  | 1.47 |
| **YOLOv8s (small)** ⭐ | **11.2** | **28.6** | **44.9** | **128.4** | **2.66** |
| YOLOv8**m** (medium) | 25.9 | 78.9 | 50.2 | 234.7 | 5.86 |
| YOLOv8**l** (large)  | 43.7 | 165.2 | 52.9 | 375.2 | 9.06 |
| YOLOv8**x** (extra)  | 68.2 | 257.8 | 53.9 | 479.1 | 12.90 |

## Nhấn mạnh trong script

- **v8n** (3.2M) quá yếu — mAP thấp, khó bắt xe máy nhỏ.
- **v8s** (11.2M) — điểm cân bằng: đủ mạnh + train được trên GPU laptop, chạy real-time.
- **v8m/l/x** — tốt hơn nhưng train mất 10-24h thay vì 5h, không đáng cho bài coursework.

## Cấu trúc scaling (giải thích thêm nếu cô hỏi)

Cùng kiến trúc CSPDarknet + PANet + Detect head, khác 2 hệ số:

| Variant | Depth multiplier | Width multiplier |
|---|---|---|
| n | 0.33 | 0.25 |
| s | 0.33 | **0.50** |
| m | 0.67 | 0.75 |
| l | 1.00 | 1.00 |
| x | 1.00 | 1.25 |

→ v8s vs v8n: cùng độ sâu, gấp đôi kênh (width) → params gấp 3.5×, mAP tăng 7.6 điểm.

## Gợi ý slide

- Bảng ở trung tâm, highlight hàng **s** (nền vàng nhạt hoặc bold).
- Ghi chú nhỏ: "Nhóm chọn s vì cân bằng accuracy - speed - train time".
