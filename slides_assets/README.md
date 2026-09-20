# Slides assets — Deck 3→7

Mỗi thư mục = 1 slide, chứa ảnh + file text hướng dẫn.

## Cấu trúc

```
slides_assets/
├── slide_3_bai_toan/
│   ├── frame_with_bbox.png       ← Frame có bbox + line từ demo video
│   └── README.md
│
├── slide_4_pipeline/
│   └── module_names.md            ← 5 tên module + màu gợi ý (không cần ảnh)
│
├── slide_5_yolov8_variants/
│   └── yolov8_comparison_table.md ← Bảng n/s/m/l/x + scaling multipliers
│
├── slide_6_data_finetune/
│   ├── class_distribution.png     ← MAIN — phân bố class (log scale)
│   ├── mAP50_per_class.png        ← MAIN — motorcycle 0.949 nổi bật
│   ├── training_curves_bonus.png  ← BONUS — mAP theo epoch
│   └── README.md
│
└── slide_7_tracking_need/
    ├── frame_1.png ... frame_4.png ← 4 frame liên tiếp (1.2s → 1.8s)
    └── README.md
```

## Nội dung ngắn cho từng slide

| Slide | Ảnh cần | Trạng thái |
|---|---|---|
| 3 — Bài toán | 1 frame có bbox + line | ✅ có sẵn |
| 4 — Pipeline 5 module | Không cần ảnh (vẽ shape) | ✅ đã ghi tên module |
| 5 — YOLOv8s variants | Không cần ảnh (dựng bảng) | ✅ đã có số liệu n/s/m/l/x |
| 6 — Data + fine-tune | 2 chart chính | ✅ có sẵn |
| 7 — Tracking cần thiết | 3-4 frame liên tiếp | ✅ đã trích 4 frame |

## Cách zip gửi

```bash
cd /home/xuand/vn_traffic_ai
zip -r slides_assets.zip slides_assets/
```

Hoặc chỉ gửi thư mục `slides_assets/` trực tiếp qua drive/telegram.
