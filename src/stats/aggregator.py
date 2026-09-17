"""Người 3 — Gom số liệu từ pipeline tracking+counting → DataFrame → CSV.

Input format (list of events, mỗi lần 1 xe cắt line):
    { "frame": 123, "time_sec": 4.10, "line": "north_south",
      "track_id": 42, "class_name": "motorcycle" }
"""
import pandas as pd
from pathlib import Path


CLASS_NAMES = ["motorcycle", "car", "bus", "truck", "bicycle"]


def events_to_df(events: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(events)
    if df.empty:
        return df
    df["time_min"] = (df["time_sec"] // 60).astype(int)
    return df


def summarize(df: pd.DataFrame) -> dict:
    """Trả dict thống kê tổng thể + per-class + per-line."""
    if df.empty:
        return {"total": 0, "per_class": {}, "per_line": {}}
    return {
        "total": len(df),
        "per_class": df["class_name"].value_counts().to_dict(),
        "per_line": df["line"].value_counts().to_dict(),
        "per_class_per_line": (df.groupby(["line", "class_name"]).size()
                               .unstack(fill_value=0).to_dict("index")),
    }


def counts_per_minute(df: pd.DataFrame) -> pd.DataFrame:
    """Bảng: hàng = phút, cột = class, giá trị = số lượt."""
    if df.empty:
        return pd.DataFrame()
    pivot = (df.groupby(["time_min", "class_name"]).size()
             .unstack(fill_value=0))
    for c in CLASS_NAMES:
        if c not in pivot.columns:
            pivot[c] = 0
    return pivot[CLASS_NAMES]


def save_csv(df: pd.DataFrame, path: str):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8-sig")
