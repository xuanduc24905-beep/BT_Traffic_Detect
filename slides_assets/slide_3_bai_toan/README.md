# Slide 3 — Bài toán

## Ảnh: `frame_with_bbox.png`

- Frame trích từ `results/videos/demo_traffic_out.mp4` (video output đã vẽ bbox 4 lớp + line đếm).
- Có bbox xanh + track_id + line đỏ ngang.
- Timestamp: giây 2 của video (chọn frame có nhiều xe qua line).

## Nếu muốn frame khác đẹp hơn

Chạy lại lệnh:
```bash
# Đổi -ss "00:00:X" thành thời điểm khác trong video
ffmpeg -y -i "results/videos/demo_traffic_out.mp4" -ss 00:00:03 -vframes 1 slides_assets/slide_3_bai_toan/frame_v2.png
```

## Có thể screenshot Streamlit thay thế

Nếu muốn UI đẹp hơn:
1. Chạy `streamlit run ui/streamlit_app.py`
2. Upload video demo, chạy pipeline
3. Screenshot phần "Video output" (có bbox + counter overlay + bảng thống kê ngay dưới)
4. Dùng screenshot đó thay `frame_with_bbox.png`
