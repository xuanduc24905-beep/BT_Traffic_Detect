"""Người 4 — Metrics đánh giá hệ thống counting.

Accuracy, MAE (Mean Absolute Error), MAPE (Mean Absolute Percentage Error)
so sánh giữa số đếm hệ thống và ground truth thủ công.
"""


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
