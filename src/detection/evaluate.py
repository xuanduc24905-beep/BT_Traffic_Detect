"""Người 1 — Đánh giá mAP trên tập test."""
import argparse
from ultralytics import YOLO


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--weights", required=True)
    ap.add_argument("--data", default="data/data.yaml")
    ap.add_argument("--imgsz", type=int, default=640)
    ap.add_argument("--split", default="test", choices=["val", "test"])
    args = ap.parse_args()

    model = YOLO(args.weights)
    metrics = model.val(data=args.data, imgsz=args.imgsz, split=args.split,
                        save_json=True)
    print(f"mAP@0.5      = {metrics.box.map50:.4f}")
    print(f"mAP@0.5:0.95 = {metrics.box.map:.4f}")
    for i, name in metrics.names.items():
        print(f"  {name:12s}  AP@0.5:0.95 = {metrics.box.maps[i]:.4f}")


if __name__ == "__main__":
    main()
