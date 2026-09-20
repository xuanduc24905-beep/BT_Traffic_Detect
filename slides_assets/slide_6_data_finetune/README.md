# Slide 6 — Dữ liệu + 2 lần fine-tune

## File chính (nhét vào slide)

| File | Vị trí trong slide |
|---|---|
| `class_distribution.png` | Trái/giữa slide — show mất cân bằng data |
| `mAP50_per_class.png` | Phải/dưới slide — kết quả cuối cùng, motorcycle 0.949 nổi bật |

## File bonus (dùng nếu tách slide phụ)

- `training_curves_bonus.png` — mAP theo epoch cho 2 lần fine-tune. Chỉ dùng nếu muốn slide phụ giải thích training process. Không bắt buộc.

## Số liệu chính khi thuyết trình

- **Dataset train:** 137k ảnh = 68k UA-DETRAC + 1,235 CanTho v19 + 1,547 vnv3.
- **Phân bố class:** car 85%, motorcycle 0.85% (mất cân bằng 100:1).
- **Fine-tune 2 vòng:**
  - Vòng 1: 50 epoch, ~5h 30m — cho v8s COCO adapt sang schema 4 lớp VN.
  - Vòng 2: 18 epoch (early stop), 2h 20m — boost xe máy bằng vnv3, LR 0.001 thấp 10×.
- **Kết quả cuối val 14k ảnh:**
  - mAP@0.5 tổng: **0.850**
  - motorcycle mAP@0.5: **0.949** ⭐ (cao nhất trong 4 class)
  - car 0.848, bus 0.911, truck 0.695

## Câu chốt cho slide

> "Cùng model YOLOv8s, không tăng params, chỉ thay đổi data + training strategy → mAP xe máy tăng vọt lên 0.949. Đây là bài học chính: **data + quy trình > model to hơn**."
