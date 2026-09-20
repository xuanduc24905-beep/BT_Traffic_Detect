"""Người 4 — Metrics đánh giá hệ thống counting + tracking (proxy).

Counting metrics: Accuracy, MAE (Mean Absolute Error),
    MAPE (Mean Absolute Percentage Error).

Tracking proxy metrics (khi không có GT tracking đầy đủ với per-frame track_id):
    - Track count (unique track_id qua line)
    - Overcount rate = (pred - gt) / gt  → dương = ID switch tiềm ẩn,
                                            âm = detection miss (recall thấp).
    - Track lifetime avg = số frame trung bình mỗi track_id tồn tại.
    - ID stability = 1 − |overcount_rate| kẹp [0, 1] — proxy cho IDF1.

Lưu ý: đây là PROXY, KHÔNG PHẢI IDF1/MOTA chuẩn (cần GT tracking per-frame).
Chi tiết xem: docs/comparison_report/... hoặc README trong src/evaluation/.
"""
from __future__ import annotations
import pandas as pd


def counting_accuracy(pred: int, gt: int) -> float:
    """1 - |pred - gt| / max(gt, 1). Kẹp về [0, 1]."""
    if gt == 0:
        return 1.0 if pred == 0 else 0.0
    return max(0.0, 1.0 - abs(pred - gt) / gt)


def mae(preds: list[int], gts: list[int]) -> float:
    assert len(preds) == len(gts) and len(preds) > 0
    return sum(abs(p - g) for p, g in zip(preds, gts)) / len(preds)


def mape(preds: list[int], gts: list[int]) -> float:
    """% — tránh chia 0 bằng cách bỏ mẫu có gt = 0."""
    pairs = [(p, g) for p, g in zip(preds, gts) if g > 0]
    if not pairs:
        return 0.0
    return 100.0 * sum(abs(p - g) / g for p, g in pairs) / len(pairs)


def tracking_proxy_from_events(events_csv: str,
                                gts: dict[str, int]) -> dict:
    """Đo tracking proxy metrics từ file events.csv.

    events.csv schema: frame, time_sec, line, direction, track_id, class_name

    Trả về dict:
        per_class: {class: {track_count, gt, overcount_rate, id_stability}}
        overall:   {track_count, gt, overcount_rate, id_stability,
                    avg_track_lifetime_frames}
    """
    df = pd.read_csv(events_csv)
    if df.empty:
        return {"per_class": {}, "overall": {
            "track_count": 0, "gt": sum(gts.values()),
            "overcount_rate": -1.0, "id_stability": 0.0,
            "avg_track_lifetime_frames": 0.0,
        }}

    # Đếm unique track_id per class (không kể qua line bao lần)
    unique_per_cls = (
        df.groupby("class_name")["track_id"].nunique().to_dict()
    )

    per_class = {}
    for cls in sorted(set(gts) | set(unique_per_cls)):
        track_n = int(unique_per_cls.get(cls, 0))
        gt_n = int(gts.get(cls, 0))
        if gt_n == 0:
            ovr = 0.0 if track_n == 0 else float("inf")
            stab = 1.0 if track_n == 0 else 0.0
        else:
            ovr = (track_n - gt_n) / gt_n
            stab = max(0.0, 1.0 - abs(ovr))
        per_class[cls] = {
            "track_count": track_n,
            "gt": gt_n,
            "overcount_rate": round(ovr, 4) if ovr != float("inf") else "inf",
            "id_stability": round(stab, 4),
        }

    total_tracks = int(df["track_id"].nunique())
    total_gt = sum(gts.values())
    if total_gt == 0:
        ovr_all = 0.0 if total_tracks == 0 else float("inf")
        stab_all = 1.0 if total_tracks == 0 else 0.0
    else:
        ovr_all = (total_tracks - total_gt) / total_gt
        stab_all = max(0.0, 1.0 - abs(ovr_all))

    # avg track lifetime = frame_max - frame_min + 1 mỗi track_id
    life = df.groupby("track_id")["frame"].agg(lambda s: s.max() - s.min() + 1)
    avg_life = float(life.mean()) if len(life) > 0 else 0.0

    return {
        "per_class": per_class,
        "overall": {
            "track_count": total_tracks,
            "gt": total_gt,
            "overcount_rate": round(ovr_all, 4) if ovr_all != float("inf") else "inf",
            "id_stability": round(stab_all, 4),
            "avg_track_lifetime_frames": round(avg_life, 1),
        },
    }


def report(preds: dict[str, int], gts: dict[str, int]) -> dict:
    """preds/gts: {'motorcycle': 120, 'car': 45, ...}"""
    classes = sorted(set(preds) | set(gts))
    p_list = [preds.get(c, 0) for c in classes]
    g_list = [gts.get(c, 0) for c in classes]
    per_class = {c: {"pred": p, "gt": g,
                     "abs_err": abs(p - g),
                     "accuracy": counting_accuracy(p, g)}
                 for c, p, g in zip(classes, p_list, g_list)}
    return {
        "per_class": per_class,
        "total_pred": sum(p_list),
        "total_gt": sum(g_list),
        "MAE": mae(p_list, g_list),
        "MAPE_percent": mape(p_list, g_list),
        "overall_accuracy": counting_accuracy(sum(p_list), sum(g_list)),
    }
