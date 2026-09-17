"""Người 3 — Biểu đồ thống kê từ DataFrame counting."""
import matplotlib.pyplot as plt
from pathlib import Path


def plot_counts_per_class(summary: dict, out_path: str):
    per_class = summary.get("per_class", {})
    if not per_class:
        print("[!] Không có dữ liệu.")
        return
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(per_class.keys(), per_class.values(), color="steelblue")
    ax.set_ylabel("Số lượt qua line")
    ax.set_title("Số lượng phương tiện theo loại")
    for i, (k, v) in enumerate(per_class.items()):
        ax.text(i, v, str(v), ha="center", va="bottom")
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def plot_counts_per_minute(pivot_df, out_path: str):
    if pivot_df.empty:
        print("[!] Không có dữ liệu.")
        return
    fig, ax = plt.subplots(figsize=(10, 5))
    pivot_df.plot(kind="line", ax=ax, marker="o")
    ax.set_xlabel("Phút")
    ax.set_ylabel("Số lượt")
    ax.set_title("Lưu lượng phương tiện theo thời gian")
    ax.legend(title="Loại xe")
    ax.grid(True, alpha=0.3)
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
