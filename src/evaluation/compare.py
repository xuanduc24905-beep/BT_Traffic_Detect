"""Người 4 — So sánh output hệ thống vs ground truth cho video test.

Ground truth JSON format:
    {
      "video": "nga_tu_01.mp4",
      "duration_sec": 300,
      "counts_by_class": {"motorcycle": 120, "car": 45, "bus": 3,
                          "truck": 2, "bicycle": 5},
      "counts_by_line": {"north_south": {"motorcycle": 60, ...}, ...}
    }
"""
import argparse
import json
from pathlib import Path
import pandas as pd

from .metrics import report


def load_pred_from_csv(csv_path: str) -> dict[str, int]:
    """CSV columns: class_name, count."""
    df = pd.read_csv(csv_path)
    return df.groupby("class_name")["count"].sum().to_dict()


def load_pred_from_events(csv_path: str) -> dict[str, int]:
    """CSV columns: frame, time_sec, line, track_id, class_name (1 dòng = 1 lượt)."""
    df = pd.read_csv(csv_path)
    return df["class_name"].value_counts().to_dict()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pred", required=True, help="CSV output từ pipeline")
    ap.add_argument("--gt", required=True, help="JSON ground truth")
    ap.add_argument("--pred-format", default="events",
                    choices=["events", "summary"])
    ap.add_argument("--out", default="results/tables/eval_report.json")
    args = ap.parse_args()

    if args.pred_format == "events":
        pred_counts = load_pred_from_events(args.pred)
    else:
        pred_counts = load_pred_from_csv(args.pred)

    with open(args.gt) as f:
        gt = json.load(f)
    gt_counts = gt["counts_by_class"]

    rep = report(pred_counts, gt_counts)

    print(f"\n{'Class':<12} {'Pred':>6} {'GT':>6} {'|Err|':>6} {'Acc':>7}")
    print("-" * 42)
    for cls, r in rep["per_class"].items():
        print(f"{cls:<12} {r['pred']:>6} {r['gt']:>6} {r['abs_err']:>6} {r['accuracy']:>7.3f}")
    print("-" * 42)
    print(f"{'TOTAL':<12} {rep['total_pred']:>6} {rep['total_gt']:>6}")
    print(f"\nMAE                = {rep['MAE']:.3f}")
    print(f"MAPE               = {rep['MAPE_percent']:.2f} %")
    print(f"Overall accuracy   = {rep['overall_accuracy']:.3f}")

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w") as f:
        json.dump(rep, f, indent=2, ensure_ascii=False)
    print(f"\n[✓] Đã lưu: {args.out}")


if __name__ == "__main__":
    main()
