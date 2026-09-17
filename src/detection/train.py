"""Người 1 — Train YOLOv8 trên merged dataset 5 lớp.

Chạy:
    python -m src.detection.train --data data/data.yaml --epochs 50 --batch 16
"""
import argparse
from pathlib import Path
from ultralytics import YOLO


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data/data.yaml")
    ap.add_argument("--pretrained", default="weights/yolov8n.pt")
    ap.add_argument("--epochs", type=int, default=50)
    ap.add_argument("--imgsz", type=int, default=640)
    ap.add_argument("--batch", type=int, default=16)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--device", default="0")
    ap.add_argument("--patience", type=int, default=15)
    ap.add_argument("--project", default="runs/detect")
    ap.add_argument("--name", default="train")
    ap.add_argument("--cache", default="disk", choices=["ram", "disk", "false"])
    args = ap.parse_args()

    model = YOLO(args.pretrained)
    model.train(
        data=args.data,
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        workers=args.workers,
        device=args.device,
        patience=args.patience,
        project=args.project,
        name=args.name,
        cache=(args.cache if args.cache != "false" else False),
        seed=42,
        exist_ok=True,
    )
    print(f"[✓] Best weight: {Path(args.project) / args.name / 'weights' / 'best.pt'}")


if __name__ == "__main__":
    main()
