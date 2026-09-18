"""Người 3 — Biểu đồ thống kê từ DataFrame counting."""
import matplotlib.pyplot as plt
import matplotlib
matplotlib.rcParams["font.family"] = "DejaVu Sans"
from pathlib import Path


def _ensure_dir(p):
    Path(p).parent.mkdir(parents=True, exist_ok=True)


def plot_counts_per_class(summary: dict, out_path: str):
    per_class = summary.get("per_class", {})
    if not per_class:
        return
    fig, ax = plt.subplots(figsize=(8, 5))
    items = sorted(per_class.items(), key=lambda x: -x[1])
    labels, values = zip(*items)
    ax.bar(labels, values, color="steelblue")
    ax.set_ylabel("Số lượt qua line")
    ax.set_title("Số lượng phương tiện theo loại")
    for i, v in enumerate(values):
        ax.text(i, v, str(v), ha="center", va="bottom")
    _ensure_dir(out_path)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def plot_counts_per_bucket(pivot_df, bucket_label: str, out_path: str,
                           kind: str = "bar"):
    """Stacked bar (mặc định) hoặc line theo bucket thời gian."""
    if pivot_df.empty:
        return
    fig, ax = plt.subplots(figsize=(10, 5))
    if kind == "bar":
        pivot_df.plot(kind="bar", stacked=True, ax=ax,
                      colormap="tab10", edgecolor="white", linewidth=0.4)
    else:
        pivot_df.plot(kind="line", ax=ax, marker="o", colormap="tab10")
    ax.set_xlabel(f"Chỉ số {bucket_label}")
    ax.set_ylabel("Số lượt")
    ax.set_title(f"Lưu lượng phương tiện theo {bucket_label}")
    ax.legend(title="Loại xe", loc="upper right")
    ax.grid(True, alpha=0.3)
    _ensure_dir(out_path)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


# Backwards-compat alias for per-minute
def plot_counts_per_minute(pivot_df, out_path: str, kind: str = "line"):
    return plot_counts_per_bucket(pivot_df, "phút", out_path, kind=kind)


def plot_heatmap(pivot_df, out_path: str, bucket_label: str = "phút"):
    """Heatmap: bucket × class."""
    if pivot_df.empty:
        return
    fig, ax = plt.subplots(figsize=(8, max(3, len(pivot_df) * 0.35)))
    im = ax.imshow(pivot_df.values, aspect="auto", cmap="YlOrRd")
    ax.set_xticks(range(len(pivot_df.columns)))
    ax.set_xticklabels(pivot_df.columns, rotation=30)
    ax.set_yticks(range(len(pivot_df.index)))
    ax.set_yticklabels(pivot_df.index)
    ax.set_xlabel("Loại xe")
    ax.set_ylabel(f"Chỉ số {bucket_label}")
    ax.set_title(f"Heatmap lưu lượng: {bucket_label} × loại xe")
    # annot
    for i in range(len(pivot_df.index)):
        for j in range(len(pivot_df.columns)):
            v = int(pivot_df.values[i, j])
            if v > 0:
                ax.text(j, i, str(v), ha="center", va="center",
                        fontsize=8,
                        color="white" if v > pivot_df.values.max() * 0.5 else "black")
    fig.colorbar(im, ax=ax, label="Số lượt")
    _ensure_dir(out_path)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def plot_cumulative(cum_df, out_path: str):
    """Đếm tích luỹ theo giây."""
    if cum_df.empty:
        return
    fig, ax = plt.subplots(figsize=(10, 5))
    cum_df.plot(ax=ax, colormap="tab10", linewidth=1.8)
    ax.set_xlabel("Thời gian (giây)")
    ax.set_ylabel("Số lượt tích luỹ")
    ax.set_title("Đếm tích luỹ phương tiện theo thời gian")
    ax.legend(title="Loại xe", loc="upper left")
    ax.grid(True, alpha=0.3)
    _ensure_dir(out_path)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def plot_line_comparison(pivot_by_line: dict, out_path: str):
    """So sánh tổng lượt qua mỗi line — pivot_by_line = {line_name: total}."""
    if not pivot_by_line:
        return
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(pivot_by_line.keys(), pivot_by_line.values(), color="darkorange")
    ax.set_ylabel("Số lượt")
    ax.set_title("So sánh lưu lượng giữa các line đếm")
    for i, (k, v) in enumerate(pivot_by_line.items()):
        ax.text(i, v, str(v), ha="center", va="bottom")
    _ensure_dir(out_path)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
