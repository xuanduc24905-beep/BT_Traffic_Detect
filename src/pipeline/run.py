"""Pipeline tích hợp end-to-end: video → detect+track → count → CSV events + video annotated.

Có thể dùng qua CLI (main) hoặc import function `run_pipeline` từ code khác (Streamlit).

CLI:
    python -m src.pipeline.run \
        --video data/test_videos/raw/nga_tu_01.mp4 \
        --weights runs/detect/train/weights/best.pt \
        --tracker bytetrack.yaml \
        --counting-config configs/counting_zones.json \
        --video-key nga_tu_01 \
        --out-csv results/tables/nga_tu_01_events.csv \
        --out-video results/videos/nga_tu_01_out.mp4
"""
import argparse
import csv
from pathlib import Path
import cv2

from src.tracking.track import track_stream
from src.tracking.counter import Counter, Line, load_lines


def draw_overlay(frame, boxes_xyxy, ids, classes, lines, counts, class_names):
    for xyxy, tid, cls in zip(boxes_xyxy, ids, classes):
        if tid is None:
            continue
        x1, y1, x2, y2 = map(int, xyxy)
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        label = f"{class_names[int(cls)]}#{int(tid)}"
        cv2.putText(frame, label, (x1, max(0, y1 - 6)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

    for line in lines:
        cv2.line(frame, line.p1, line.p2, (0, 0, 255), 2)
        cv2.putText(frame, line.name, line.p1,
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

    y = 30
    for ln, per_cls in counts.items():
        total = sum(per_cls.values())
        cv2.putText(frame, f"{ln}: {total}", (10, y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        y += 24
    return frame


def run_pipeline(video: str, weights: str, lines: list,
                 tracker: str = "bytetrack.yaml",
                 conf: float = 0.25, iou: float = 0.5, imgsz: int = 640,
                 out_csv: str | None = None,
                 out_video: str | None = None,
                 progress_cb=None):
    """Chạy pipeline. Trả về (events list, counter.to_dict()).

    progress_cb: hàm nhận (frame_idx, total_frames) — dùng cho Streamlit progress bar.
    """
    cap = cv2.VideoCapture(video)
    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()

    counter = Counter(lines=lines)

    writer = None
    if out_video:
        Path(out_video).parent.mkdir(parents=True, exist_ok=True)
        writer = cv2.VideoWriter(
            out_video, cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))

    events = []
    prev_counts_snapshot = {ln.name: dict() for ln in lines}
    class_names = None

    for frame_idx, res in enumerate(track_stream(
            weights, video, tracker=tracker,
            conf=conf, iou=iou, imgsz=imgsz)):

        if class_names is None:
            class_names = res.names

        if res.boxes.id is None:
            frame = res.orig_img.copy() if writer else None
        else:
            boxes = res.boxes.xyxy.cpu().numpy()
            ids = res.boxes.id.cpu().numpy()
            classes = res.boxes.cls.cpu().numpy()
            counter.update(frame_idx, boxes, ids, classes)
            frame = res.orig_img.copy() if writer else None

            for ln_name, per_cls in counter.counts.items():
                prev = prev_counts_snapshot[ln_name]
                for cls_id, cnt in per_cls.items():
                    delta = cnt - prev.get(cls_id, 0)
                    for _ in range(delta):
                        events.append({
                            "frame": frame_idx,
                            "time_sec": round(frame_idx / fps, 3),
                            "line": ln_name,
                            "track_id": -1,
                            "class_name": class_names[int(cls_id)],
                        })
                prev_counts_snapshot[ln_name] = dict(per_cls)

            if writer is not None:
                frame = draw_overlay(frame, boxes, ids, classes, lines,
                                     counter.counts, class_names)

        if writer is not None and frame is not None:
            writer.write(frame)

        if progress_cb is not None:
            progress_cb(frame_idx + 1, total_frames)

    if writer is not None:
        writer.release()

    if out_csv:
        Path(out_csv).parent.mkdir(parents=True, exist_ok=True)
        with open(out_csv, "w", newline="", encoding="utf-8-sig") as f:
            w_csv = csv.DictWriter(f, fieldnames=["frame", "time_sec", "line",
                                                  "track_id", "class_name"])
            w_csv.writeheader()
            w_csv.writerows(events)

    return events, counter.to_dict(), class_names


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--weights", required=True)
    ap.add_argument("--tracker", default="bytetrack.yaml")
    ap.add_argument("--counting-config", default="configs/counting_zones.json")
    ap.add_argument("--video-key", required=True, help="key trong counting_zones.json")
    ap.add_argument("--conf", type=float, default=0.25)
    ap.add_argument("--iou", type=float, default=0.5)
    ap.add_argument("--imgsz", type=int, default=640)
    ap.add_argument("--out-csv", required=True)
    ap.add_argument("--out-video", default=None)
    args = ap.parse_args()

    lines = load_lines(args.counting_config, args.video_key)
    events, totals, _ = run_pipeline(
        video=args.video, weights=args.weights, lines=lines,
        tracker=args.tracker, conf=args.conf, iou=args.iou, imgsz=args.imgsz,
        out_csv=args.out_csv, out_video=args.out_video,
    )
    print(f"[✓] {len(events)} events → {args.out_csv}")
    print(f"[✓] Totals: {totals}")


if __name__ == "__main__":
    main()
