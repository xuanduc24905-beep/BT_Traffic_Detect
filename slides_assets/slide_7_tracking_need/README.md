# Slide 7 — Vì sao detection chưa đủ để đếm

## 4 ảnh frame liên tiếp

- `frame_1.png` → `frame_4.png` — trích từ demo_traffic_out.mp4 tại giây 1.2, 1.4, 1.6, 1.8.
- Cùng cảnh, xe di chuyển tiến về phía line đếm.
- Đã vẽ sẵn bbox + line đỏ.

## Cách trình bày 4 ảnh trên slide

Xếp 4 ảnh **thành 1 hàng ngang** (hoặc grid 2x2), highlight cùng 1 xe qua các frame bằng vòng tròn/mũi tên màu:

```
[frame_1] → [frame_2] → [frame_3] → [frame_4]
     xe A        xe A        xe A        xe A qua line
```

Thêm text overlay:
- "Nếu chỉ dùng detection thuần → mỗi frame đếm lại xe A = 4 lần cho cùng 1 xe"
- "Cần track_id giữ xe A xuyên frame → chỉ đếm 1 lần khi cắt line"

## Nếu muốn frame khác

Video đã dùng: `results/videos/demo_traffic_out.mp4` — có bbox sẵn.

Chạy lại với thời điểm khác:
```bash
for i in 1 2 3 4; do
    ffmpeg -y -i "results/videos/demo_traffic_out.mp4" \\
        -ss "3.$((i*2))" -vframes 1 \\
        "slides_assets/slide_7_tracking_need/frame_$i.png"
done
```

## Alternative: sơ đồ vẽ tay

Nếu 4 frame trông rối, có thể vẽ sơ đồ đơn giản:

```
Frame 1:     [xe A]------->  |  (line)
Frame 2:       [xe A]----->  |
Frame 3:         [xe A]--->  |
Frame 4:           [xe A]--->|  ← CẮT LINE

Detection thuần:  đếm 4 lần
+ Tracking:       đếm 1 lần (khi cắt line)
```
