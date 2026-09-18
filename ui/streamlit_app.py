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
from src.stats.aggregator import (
    events_to_df, summarize, counts_per_bucket, flow_rate, peak_period,
    cumulative_counts, format_bucket_label,
)
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

            # --- Bucket selector ---
            BUCKETS = {"30 giây": 30, "1 phút": 60, "5 phút": 300,
                       "15 phút": 900, "30 phút": 1800, "1 giờ": 3600}
            bucket_choice = st.selectbox("Chia thời gian theo",
                                         list(BUCKETS.keys()),
                                         index=1)
            bucket_sec = BUCKETS[bucket_choice]
            pivot = counts_per_bucket(df_enriched, bucket_sec)

            # --- Metrics tổng thể ---
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Tổng lượt", summ["total"])
            c2.metric("Số loại xe", len(summ["per_class"]))
            c3.metric("Loại nhiều nhất",
                      max(summ["per_class"], key=summ["per_class"].get))
            c4.metric("Thời lượng (s)", f"{summ['duration_sec']:.1f}")

            # --- Flow rate ---
            st.markdown("#### 🚗 Tốc độ lưu lượng")
            fr_min = flow_rate(df_enriched, unit="minute")
            fr_hour = flow_rate(df_enriched, unit="hour")
            fc1, fc2 = st.columns(2)
            fc1.metric("Tổng xe/phút", fr_min.get("total", 0))
            fc2.metric("Tổng xe/giờ", fr_hour.get("total", 0))

            if fr_hour.get("per_class"):
                fr_df = pd.DataFrame([
                    {"class": k, "xe/phút": fr_min["per_class"].get(k, 0),
                     "xe/giờ": fr_hour["per_class"].get(k, 0)}
                    for k in fr_hour["per_class"]
                ])
                st.dataframe(fr_df, use_container_width=True)

            # --- Peak period ---
            peak = peak_period(df_enriched, bucket_sec)
            if peak:
                st.markdown("#### 📈 Khung giờ cao điểm")
                pc1, pc2, pc3 = st.columns(3)
                pc1.metric(f"Bucket cao điểm ({bucket_choice})",
                           f"#{peak['peak_bucket']}")
                pc2.metric("Từ giây",
                           f"{peak['peak_start_sec']}–{peak['peak_end_sec']}")
                pc3.metric("Số lượt trong bucket", peak["peak_total"])

            # --- Chart theo bucket ---
            st.markdown(f"#### 📊 Lưu lượng theo {bucket_choice}")
            if pivot.empty:
                st.caption(f"Video quá ngắn để chia theo {bucket_choice}.")
            else:
                chart_kind = st.radio("Kiểu biểu đồ",
                                      ["Line", "Bar chồng"], horizontal=True)
                if chart_kind == "Line":
                    st.line_chart(pivot)
                else:
                    st.bar_chart(pivot)

            # --- Heatmap ---
            st.markdown("#### 🔥 Heatmap thời gian × loại xe")
            if not pivot.empty:
                # Streamlit dùng dataframe styling để hiển thị màu
                st.dataframe(
                    pivot.style.background_gradient(cmap="YlOrRd", axis=None),
                    use_container_width=True,
                )

            # --- Cumulative ---
            st.markdown("#### 📈 Đếm tích luỹ theo thời gian")
            cum = cumulative_counts(df_enriched)
            if not cum.empty:
                st.line_chart(cum)

            # --- Per class ---
            st.markdown("#### 🚦 Số lượng theo loại xe (tổng)")
            counts_df = pd.DataFrame(
                {"class_name": list(summ["per_class"].keys()),
                 "count": list(summ["per_class"].values())}
            ).sort_values("count", ascending=False)
            st.bar_chart(counts_df.set_index("class_name"))

            # --- Per line ---
            if len(summ["per_line"]) > 1:
                st.markdown("#### 🛣 So sánh lưu lượng giữa các line")
                line_df = pd.DataFrame(
                    {"line": list(summ["per_line"].keys()),
                     "count": list(summ["per_line"].values())}
                )
                st.bar_chart(line_df.set_index("line"))

            # --- Event log ---
            st.markdown("#### 📋 Event log")
            st.dataframe(df_enriched, use_container_width=True, height=250)

            # --- Downloads ---
            dc1, dc2, dc3 = st.columns(3)
            with dc1:
                st.download_button("Events CSV",
                                   df.to_csv(index=False).encode("utf-8-sig"),
                                   file_name="events.csv")
            with dc2:
                st.download_button("Summary CSV",
                                   counts_df.to_csv(index=False).encode("utf-8-sig"),
                                   file_name="summary.csv")
            with dc3:
                if not pivot.empty:
                    st.download_button(
                        f"Bucket {bucket_choice} CSV",
                        pivot.to_csv().encode("utf-8-sig"),
                        file_name=f"bucket_{bucket_sec}s.csv")

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
