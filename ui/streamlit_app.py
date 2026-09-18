"""Streamlit UI cho hệ thống đếm phương tiện.

Chạy:
    cd /home/xuand/vn_traffic_ai
    conda activate yolov8_ft
    streamlit run ui/streamlit_app.py
"""
import json
import sys
import tempfile
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.pipeline.run import run_pipeline
from src.tracking.counter import Line
from src.stats.aggregator import events_to_df, summarize, counts_per_minute
from src.evaluation.metrics import report as eval_report


st.set_page_config(page_title="VN Traffic AI", page_icon="🚦", layout="wide")

# ---------- Sidebar ----------
st.sidebar.title("⚙️ Cấu hình")

WEIGHTS_DIR = ROOT / "weights"
available_weights = sorted([str(p.relative_to(ROOT)) for p in WEIGHTS_DIR.glob("*.pt")])
runs_weights = sorted([str(p.relative_to(ROOT))
                       for p in (ROOT / "runs").rglob("best.pt")]) if (ROOT / "runs").exists() else []
all_weights = available_weights + runs_weights

if not all_weights:
    st.sidebar.error("Không tìm thấy file .pt nào trong weights/ hoặc runs/")
    st.stop()

weights_path = st.sidebar.selectbox("Model weights", all_weights, index=0)
tracker = st.sidebar.radio("Tracker", ["bytetrack.yaml", "botsort.yaml"])
conf = st.sidebar.slider("Confidence threshold", 0.1, 0.9, 0.3, 0.05)
iou = st.sidebar.slider("IoU threshold (NMS)", 0.1, 0.9, 0.5, 0.05)
imgsz = st.sidebar.selectbox("Image size", [416, 512, 640, 768], index=2)

st.sidebar.markdown("---")
st.sidebar.markdown("**Line đếm**")
line_y_pct = st.sidebar.slider("Vị trí line (% chiều cao)", 10, 90, 50, 5)
line_direction = st.sidebar.radio("Hướng line", ["horizontal", "vertical"])

# ---------- Main ----------
st.title("🚦 VN Traffic AI — Đếm và phân loại phương tiện")
st.caption("Detection + Tracking (ByteTrack/BoT-SORT) + Counting theo line")

tab_run, tab_stats, tab_eval = st.tabs(["▶️ Chạy pipeline", "📊 Thống kê", "📐 Đánh giá"])

# ---------- Tab 1: Run ----------
with tab_run:
    uploaded = st.file_uploader("Upload video giao thông (mp4/avi/mov)",
                                type=["mp4", "avi", "mov"])

    col_a, col_b = st.columns([1, 1])
    with col_a:
        preview_video = st.empty()
    with col_b:
        info_placeholder = st.empty()

    if uploaded:
        # Save uploaded to temp
        tmp_dir = Path(tempfile.gettempdir()) / "vn_traffic_ai_uploads"
        tmp_dir.mkdir(parents=True, exist_ok=True)
        tmp_video = tmp_dir / uploaded.name
        tmp_video.write_bytes(uploaded.read())
        st.session_state["tmp_video"] = str(tmp_video)
        preview_video.video(str(tmp_video))

        # get video dimensions
        import cv2
        cap = cv2.VideoCapture(str(tmp_video))
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS) or 25
        n_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.release()
        info_placeholder.info(
            f"**{w}×{h}** @ **{fps:.1f}** fps · **{n_frames}** frames · "
            f"**{n_frames/fps:.1f}s**"
        )
        st.session_state["video_meta"] = dict(w=w, h=h, fps=fps, n_frames=n_frames)

    if st.button("🚀 Chạy pipeline", type="primary", disabled="tmp_video" not in st.session_state):
        meta = st.session_state["video_meta"]
        w, h = meta["w"], meta["h"]

        # Build line
        if line_direction == "horizontal":
            y = int(h * line_y_pct / 100)
            line = Line(name="line_1", p1=(50, y), p2=(w - 50, y))
        else:
            x = int(w * line_y_pct / 100)
            line = Line(name="line_1", p1=(x, 50), p2=(x, h - 50))

        out_dir = ROOT / "results"
        out_video = out_dir / "videos" / f"streamlit_{Path(st.session_state['tmp_video']).stem}_out.mp4"
        out_csv = out_dir / "tables" / f"streamlit_{Path(st.session_state['tmp_video']).stem}_events.csv"

        progress = st.progress(0, text="Chạy pipeline...")

        def _cb(cur, total):
            if total > 0:
                progress.progress(min(cur / total, 1.0),
                                  text=f"Frame {cur}/{total}")

        with st.spinner("Detecting + tracking + counting..."):
            events, totals, class_names = run_pipeline(
                video=st.session_state["tmp_video"],
                weights=str(ROOT / weights_path),
                lines=[line],
                tracker=tracker,
                conf=conf, iou=iou, imgsz=imgsz,
                out_csv=str(out_csv),
                out_video=str(out_video),
                progress_cb=_cb,
            )

        progress.empty()
        st.success(f"Xong! {len(events)} lượt qua line.")
        st.session_state["events_csv"] = str(out_csv)
        st.session_state["out_video"] = str(out_video)
        st.session_state["totals"] = totals
        st.session_state["class_names"] = class_names

    if "out_video" in st.session_state:
        st.markdown("### 🎬 Video output")
        st.video(st.session_state["out_video"])
        with open(st.session_state["out_video"], "rb") as f:
            st.download_button("Download video", f, file_name=Path(st.session_state["out_video"]).name)

# ---------- Tab 2: Stats ----------
with tab_stats:
    if "events_csv" not in st.session_state:
        st.info("Chạy pipeline ở tab đầu tiên để có dữ liệu thống kê.")
    else:
        df = pd.read_csv(st.session_state["events_csv"])
        if df.empty:
            st.warning("Không có event nào (0 xe qua line). Thử giảm confidence hoặc đổi vị trí line.")
        else:
            df_enriched = events_to_df(df.to_dict("records"))
            summ = summarize(df_enriched)

            col1, col2, col3 = st.columns(3)
            col1.metric("Tổng lượt qua line", summ["total"])
            col2.metric("Số loại xe", len(summ["per_class"]))
            col3.metric("Loại nhiều nhất",
                        max(summ["per_class"], key=summ["per_class"].get))

            st.markdown("#### Số lượng theo loại xe")
            counts_df = pd.DataFrame(
                {"class_name": list(summ["per_class"].keys()),
                 "count": list(summ["per_class"].values())}
            ).sort_values("count", ascending=False)
            st.bar_chart(counts_df.set_index("class_name"))

            st.markdown("#### Lưu lượng theo phút")
            per_min = counts_per_minute(df_enriched)
            if per_min.empty:
                st.caption("Video quá ngắn để chia theo phút.")
            else:
                st.line_chart(per_min)

            st.markdown("#### Event log")
            st.dataframe(df_enriched, use_container_width=True, height=300)

            st.download_button("Download events CSV",
                               df.to_csv(index=False).encode("utf-8-sig"),
                               file_name="events.csv")
            st.download_button("Download summary CSV",
                               counts_df.to_csv(index=False).encode("utf-8-sig"),
                               file_name="summary.csv")

# ---------- Tab 3: Eval ----------
with tab_eval:
    if "events_csv" not in st.session_state:
        st.info("Chạy pipeline trước để có kết quả dự đoán.")
    else:
        st.markdown("Upload JSON ground truth (đếm tay). "
                    "Cấu trúc: `{'counts_by_class': {'car': N, 'bus': N, ...}}`")

        gt_file = st.file_uploader("Ground truth JSON", type=["json"], key="gt")

        col_x, col_y = st.columns(2)
        with col_x:
            st.markdown("#### Hoặc điền tay bên dưới")
            df = pd.read_csv(st.session_state["events_csv"])
            preds = df["class_name"].value_counts().to_dict() if not df.empty else {}
            gt_manual = {}
            for cls in ["motorcycle", "car", "bus", "truck", "van", "others", "bicycle"]:
                gt_manual[cls] = st.number_input(f"GT — {cls}", min_value=0,
                                                 value=preds.get(cls, 0), step=1)

        with col_y:
            if gt_file is not None:
                gt_json = json.loads(gt_file.read())
                gt_counts = gt_json.get("counts_by_class", {})
            else:
                gt_counts = {k: v for k, v in gt_manual.items() if v > 0}

            pred_counts = df["class_name"].value_counts().to_dict() if not df.empty else {}
            if not gt_counts:
                st.warning("Chưa có GT.")
            else:
                rep = eval_report(pred_counts, gt_counts)
                st.markdown("#### Kết quả đánh giá")

                rows = []
                for cls, r in rep["per_class"].items():
                    rows.append({"Class": cls, "Pred": r["pred"], "GT": r["gt"],
                                 "|Err|": r["abs_err"], "Accuracy": r["accuracy"]})
                st.dataframe(pd.DataFrame(rows), use_container_width=True)

                c1, c2, c3 = st.columns(3)
                c1.metric("Overall Accuracy", f"{rep['overall_accuracy']:.3f}")
                c2.metric("MAE", f"{rep['MAE']:.2f}")
                c3.metric("MAPE (%)", f"{rep['MAPE_percent']:.2f}")

                st.download_button("Download eval report (JSON)",
                                   json.dumps(rep, indent=2, ensure_ascii=False),
                                   file_name="eval_report.json")

st.markdown("---")
st.caption("VN Traffic AI · Chủ đề 10 — Detection + Tracking + Counting")
