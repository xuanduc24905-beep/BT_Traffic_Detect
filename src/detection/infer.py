"""Người 1 — Inference trên ảnh/video, trả về detections (bbox + class + conf)."""
import argparse
from pathlib import Path
from ultralytics import YOLO


def load_model(weights: str, device: str = "0"):
    model = YOLO(weights)
    model.to(device)
    return model


def predict(model, source, conf: float = 0.25, iou: float = 0.5, imgsz: int = 640):
    """Wrapper — trả về generator kết quả để pipeline dùng."""
    return model.predict(source=source, conf=conf, iou=iou, imgsz=imgsz,
                         stream=True, verbose=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--weights", required=True)
    ap.add_argument("--source", required=True, help="ảnh, thư mục, hoặc video")
    ap.add_argument("--conf", type=float, default=0.25)
    ap.add_argument("--iou", type=float, default=0.5)
    ap.add_argument("--save", action="store_true")
    args = ap.parse_args()

    model = load_model(args.weights)
    results = model.predict(source=args.source, conf=args.conf, iou=args.iou,
                            save=args.save, verbose=True)
    print(f"[✓] Đã xử lý {len(results)} frame/ảnh.")


if __name__ == "__main__":
    main()
