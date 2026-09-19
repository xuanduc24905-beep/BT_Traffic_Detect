"""Người 2 — Wrapper tracking: YOLO + ByteTrack/BoT-SORT (built-in Ultralytics).

Ultralytics đã có sẵn 2 tracker: 'bytetrack.yaml' và 'botsort.yaml'.
Wrapper này trả về stream các frame kèm tracking ID để module counter dùng.
"""
from ultralytics import YOLO


def track_stream(weights: str, source: str,
                 tracker: str = "bytetrack.yaml",
                 conf: float = 0.25, iou: float = 0.5,
                 imgsz: int = 640, device: str = "0",
                 half: bool = False):
    """Yield từng frame result có `.boxes.id` (tracking ID).

    result.boxes có các thuộc tính:
      - xyxy: (N, 4) — box toạ độ pixel
      - conf: (N,) — confidence
      - cls: (N,) — class id
      - id: (N,) — tracking id (có thể None với box vừa xuất hiện)

    half=True bật FP16 inference (~1.3-1.5× nhanh hơn trên GPU Ada/Ampere).
    """
    model = YOLO(weights)
    return model.track(
        source=source,
        tracker=tracker,
        conf=conf, iou=iou, imgsz=imgsz,
        device=device,
        half=half,
        stream=True, persist=True, verbose=False,
    )


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--weights", required=True)
    ap.add_argument("--source", required=True)
    ap.add_argument("--tracker", default="bytetrack.yaml",
                    choices=["bytetrack.yaml", "botsort.yaml"])
    args = ap.parse_args()

    for i, res in enumerate(track_stream(args.weights, args.source, args.tracker)):
        if res.boxes.id is None:
            continue
        n = len(res.boxes)
        print(f"frame {i:5d} n_track = {n} ids = {res.boxes.id.tolist()[:5]}...")
