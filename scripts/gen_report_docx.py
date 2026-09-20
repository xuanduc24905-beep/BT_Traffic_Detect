"""Sinh file Word (.docx) từ dữ liệu báo cáo — nhúng ảnh chart để đưa vào PPT.

Output: docs/comparison_report/BAO_CAO_BASELINE_VS_IMPROVED.docx
"""
from __future__ import annotations

import csv
import json
from pathlib import Path
from collections import defaultdict

from docx import Document
from docx.shared import Cm, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

ROOT = Path(__file__).resolve().parent.parent
CHARTS = ROOT / "docs/comparison_report/charts"
OUT = ROOT / "docs/comparison_report/BAO_CAO_BASELINE_VS_IMPROVED.docx"

CLASS_ORDER = ["motorcycle", "car", "bus", "truck"]
CLASS_VN = {"motorcycle": "xe may", "car": "o to",
            "bus": "xe buyt", "truck": "xe tai"}
PER_CLASS_VAL = {
    "motorcycle": {"P": 0.858, "R": 0.917, "mAP50": 0.949, "mAP50_95": 0.609},
    "car":        {"P": 0.899, "R": 0.794, "mAP50": 0.848, "mAP50_95": 0.629},
    "bus":        {"P": 0.917, "R": 0.819, "mAP50": 0.911, "mAP50_95": 0.772},
    "truck":      {"P": 0.803, "R": 0.631, "mAP50": 0.695, "mAP50_95": 0.543},
}


def load_csv(path: Path) -> dict:
    rows = list(csv.DictReader(path.open()))
    return {k.strip(): [float(r[k]) for r in rows] for k in rows[0]}


def peak(d: dict) -> dict:
    import numpy as np
    i = int(np.argmax(d["metrics/mAP50(B)"]))
    return {
        "epoch": int(d["epoch"][i]),
        "P": d["metrics/precision(B)"][i],
        "R": d["metrics/recall(B)"][i],
        "mAP50": d["metrics/mAP50(B)"][i],
        "mAP50_95": d["metrics/mAP50-95(B)"][i],
    }


def set_cell_shading(cell, fill_hex: str):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), fill_hex)
    tc_pr.append(shd)


def add_heading(doc, text, level=1):
    h = doc.add_heading(text, level=level)
    for run in h.runs:
        run.font.color.rgb = RGBColor(0x1F, 0x3B, 0x6E)
    return h


def add_para(doc, text, bold=False, italic=False, size=11):
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.bold = bold
    run.italic = italic
    run.font.size = Pt(size)
    return p


def add_bullets(doc, items):
    for it in items:
        doc.add_paragraph(it, style="List Bullet")


def add_table(doc, headers, rows, header_fill="1F3B6E"):
    tbl = doc.add_table(rows=1 + len(rows), cols=len(headers))
    tbl.style = "Light Grid Accent 1"
    hdr = tbl.rows[0].cells
    for i, h in enumerate(headers):
        hdr[i].text = h
        set_cell_shading(hdr[i], header_fill)
        for run in hdr[i].paragraphs[0].runs:
            run.bold = True
            run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
            run.font.size = Pt(10)
    for r_idx, row in enumerate(rows, start=1):
        for c_idx, val in enumerate(row):
            tbl.rows[r_idx].cells[c_idx].text = str(val)
            for run in tbl.rows[r_idx].cells[c_idx].paragraphs[0].runs:
                run.font.size = Pt(10)
    return tbl


def add_image(doc, path: Path, width_cm=15.5, caption=None):
    if not path.exists():
        doc.add_paragraph(f"[Thieu anh: {path.name}]")
        return
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run().add_picture(str(path), width=Cm(width_cm))
    if caption:
        cap = doc.add_paragraph(caption)
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for run in cap.runs:
            run.italic = True
            run.font.size = Pt(9)
            run.font.color.rgb = RGBColor(0x55, 0x55, 0x55)


def pct(a, b): return (a - b) / b * 100


def main():
    print("[load] training curves + counting...")
    bl = load_csv(ROOT / "runs/detect/runs/detect/train_v8s_4cls/results.csv")
    im = load_csv(ROOT / "runs/detect/runs/detect/train_v8s_ft_vnv3/results.csv")
    bl_p, im_p = peak(bl), peak(im)
    counting = json.loads((ROOT / "results/tables/eval_counting_2pipelines.json").read_text())
    gt = counting["gt"]
    bl_c, im_c = counting["baseline"], counting["improved"]
    speedup = im_c["fps"] / bl_c["fps"]

    print("[count] class distribution...")
    cls_counts = defaultdict(int)
    for f in (ROOT / "data/merged/labels/train").glob("*.txt"):
        for line in f.read_text().splitlines():
            if line.strip():
                cls_counts[int(line.split()[0])] += 1

    doc = Document()

    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(11)

    # ================== TIÊU ĐỀ ==================
    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title.add_run("BÁO CÁO SO SÁNH: BASELINE vs IMPROVED PIPELINE")
    run.bold = True
    run.font.size = Pt(18)
    run.font.color.rgb = RGBColor(0x1F, 0x3B, 0x6E)

    sub = doc.add_paragraph()
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = sub.add_run("Chủ đề 10 — Đếm & phân loại phương tiện giao thông")
    r.italic = True; r.font.size = Pt(13)

    info = doc.add_paragraph()
    info.alignment = WD_ALIGN_PARAGRAPH.CENTER
    info.add_run("Nhóm: Đức Đặng  |  Ngày: 2026-09-19  |  Model: YOLOv8s (11.2M params, 28.6 GFLOPs)").font.size = Pt(10)

    doc.add_paragraph("_" * 80).alignment = WD_ALIGN_PARAGRAPH.CENTER

    # ================== 0. EXECUTIVE SUMMARY ==================
    add_heading(doc, "TÓM TẮT ĐIỀU HÀNH (Executive Summary)", 1)
    add_bullets(doc, [
        "2 pipeline cùng kiến trúc YOLOv8s — khác duy nhất ở trọng số & dữ liệu huấn luyện.",
        "Baseline = tải yolov8s.pt COCO gốc, chạy thẳng — không huấn luyện.",
        "Improved = fine-tune 2 lần trên 137k ảnh Việt Nam (UA-DETRAC + CanTho v19 + Vietnamese vehicle v3).",
        f"Kết quả trên val set (Improved): mAP@0.5 = {im_p['mAP50']:.3f}, mAP@0.5:0.95 = {im_p['mAP50_95']:.3f}.",
        "Điểm sáng nhất: motorcycle mAP@0.5 = 0.949 (cao nhất 4 class) nhờ boost vnv3 (+2,232 bbox xe máy).",
        f"Tốc độ inference: Improved nhanh hơn {speedup:.2f}x ({bl_c['fps']:.1f} FPS -> {im_c['fps']:.1f} FPS).",
    ])

    # ================== 1. BỐI CẢNH ==================
    add_heading(doc, "1. Bối cảnh & mục tiêu", 1)
    add_para(doc, "Bài toán yêu cầu detect + track + count 4 lớp phương tiện giao thông trong video Việt Nam. "
                  "Nhóm so sánh 2 phương pháp tiếp cận:")
    add_table(doc,
              ["#", "Pipeline", "Model weights", "Có huấn luyện?", "Output"],
              [
                  ["1", "Baseline", "yolov8s.pt (COCO pretrained)", "Không", "80 lớp (lọc 4 phương tiện)"],
                  ["2", "Improved", "train_v8s_ft_vnv3/best.pt", "Có (2 lần fine-tune)", "4 lớp VN"],
              ])
    add_para(doc, "Cùng kiến trúc YOLOv8s → khác biệt chỉ ở dữ liệu + huấn luyện → so sánh công bằng.", italic=True)
    add_para(doc, "Giả thuyết: Model fine-tune trên dữ liệu VN sẽ vượt trội về khả năng bắt xe máy — vấn đề mà COCO gốc yếu.")

    # ================== 2. DỮ LIỆU ==================
    add_heading(doc, "2. Dữ liệu huấn luyện", 1)

    add_heading(doc, "2.1 Nguồn dữ liệu (3 nguồn hợp nhất)", 2)
    add_table(doc,
              ["Nguồn", "Vai trò chính", "Ảnh gốc", "Ghi chú"],
              [
                  ["UA-DETRAC (TQ)", "Car, bus, truck", "~140k", "Camera cao, benchmark chuẩn"],
                  ["Vehicle Vietnam-CanTho v19", "Motorcycle chính", "1,235", "Đường phố Cần Thơ"],
                  ["Vietnamese vehicle v3", "Boost motorcycle", "1,547", "+2,232 bbox xe máy (vòng 2)"],
              ])

    add_heading(doc, "2.2 Phân bố class sau merge", 2)
    add_image(doc, CHARTS / "class_distribution.png",
              caption="Chart 1 — Phân bố class trong tập train (log scale, mỗi lớp 1 màu)")

    total_bbox = sum(cls_counts.values())
    add_table(doc,
              ["Class ID", "Tên lớp", "Bbox", "Tỉ lệ (%)"],
              [
                  ["0", "motorcycle (xe máy)", f"{cls_counts[0]:,}", f"{cls_counts[0]/total_bbox*100:.2f}%"],
                  ["1", "car (ô tô)", f"{cls_counts[1]:,}", f"{cls_counts[1]/total_bbox*100:.2f}%"],
                  ["2", "bus (xe buýt)", f"{cls_counts[2]:,}", f"{cls_counts[2]/total_bbox*100:.2f}%"],
                  ["3", "truck (xe tải)", f"{cls_counts[3]:,}", f"{cls_counts[3]/total_bbox*100:.2f}%"],
                  ["", "TỔNG", f"{total_bbox:,}", "100%"],
              ])
    add_para(doc, "Nhận xét:", bold=True)
    add_bullets(doc, [
        f"Car chiếm ~{cls_counts[1]/total_bbox*100:.0f}% → mất cân bằng nặng (car gấp ~{cls_counts[1]/cls_counts[0]:.0f}x xe máy).",
        f"Motorcycle chỉ {cls_counts[0]/total_bbox*100:.2f}% dù đã boost vnv3 — vẫn là class khó nhất.",
        "Đó là lý do phần fine-tune tập trung boost xe máy.",
    ])

    # ================== 3. QUY TRÌNH HUẤN LUYỆN ==================
    add_heading(doc, "3. Quy trình huấn luyện (Improved)", 1)

    add_heading(doc, "3.1 Fine-tune lần 1 — train_v8s_4cls", 2)
    add_bullets(doc, [
        "Init: yolov8s.pt (COCO pretrained, reset head 80→4 lớp).",
        "Config: 50 epoch, batch 32, imgsz 512, LR default (0.01).",
        "Thời gian: ~5h 30m trên RTX 3500 Ada 12GB.",
        f"Best: epoch {bl_p['epoch']} — mAP50 = {bl_p['mAP50']:.4f}, mAP50-95 = {bl_p['mAP50_95']:.4f}.",
    ])

    add_heading(doc, "3.2 Fine-tune lần 2 — train_v8s_ft_vnv3 (Continual)", 2)
    add_bullets(doc, [
        "Init: best.pt lần 1 (KHÔNG phải COCO).",
        "Config: 25 epoch (early stop ở 18), batch 32, imgsz 512, LR 0.001 (thấp 10x), patience 8.",
        "Thêm dữ liệu: 1,547 ảnh vnv3 (boost motorcycle).",
        "Thời gian thực tế: 2h 20m.",
        f"Best: epoch {im_p['epoch']} — mAP50 = {im_p['mAP50']:.4f}, mAP50-95 = {im_p['mAP50_95']:.4f}.",
    ])
    add_para(doc,
             "Vì sao LR thấp? Fine-tune tiếp từ checkpoint đã hội tụ ⇒ LR default sẽ phá kiến thức cũ "
             "(catastrophic forgetting). LR 0.001 giữ nguyên feature backbone, chỉ tinh chỉnh nhẹ.",
             italic=True)

    add_image(doc, CHARTS / "gen_time.png",
              caption="Chart 2 — Thời gian huấn luyện tích luỹ 2 lần fine-tune")

    # ================== 4. DETECTION QUALITY ==================
    add_heading(doc, "4. Kết quả detection quality (val set 14,344 ảnh)", 1)

    add_heading(doc, "4.1 mAP@0.5 mỗi lớp — điểm nhấn báo cáo", 2)
    add_image(doc, CHARTS / "mAP50_per_class.png",
              caption="Chart 3 — mAP@0.5 mỗi lớp, motorcycle 0.949 đứng đầu")

    add_para(doc, "Detection metrics per class:", bold=True)
    rows = []
    for cls in CLASS_ORDER:
        v = PER_CLASS_VAL[cls]
        rows.append([f"{cls}",
                     f"{v['P']:.3f}", f"{v['R']:.3f}",
                     f"{v['mAP50']:.3f}", f"{v['mAP50_95']:.3f}"])
    rows.append(["all", "0.869", "0.790", "0.850", "0.638"])
    add_table(doc, ["Class", "Precision", "Recall", "mAP@0.5", "mAP@0.5:0.95"], rows)

    add_image(doc, CHARTS / "per_class_val_metrics.png", width_cm=16,
              caption="Chart 4 — 4 metric × 4 class, cùng lớp = cùng màu")

    add_para(doc, "Nhận xét chính:", bold=True)
    add_bullets(doc, [
        "Motorcycle mAP@0.5 = 0.949 — cao nhất, chứng minh hiệu quả của việc thêm vnv3.",
        "Motorcycle Recall = 0.917 — bắt được 91.7% xe máy trong val set (chỉ miss ~8%).",
        "Truck yếu nhất (mAP@0.5 = 0.695) — do UA-DETRAC gộp van → truck, 2 loại có ngoại hình khác nhau ⇒ confusion.",
    ])

    add_heading(doc, "4.2 So sánh 2 lần fine-tune (training curves)", 2)
    add_image(doc, CHARTS / "training_curves.png", width_cm=16,
              caption="Chart 5 — mAP@0.5 & mAP@0.5:0.95 qua epoch")
    add_image(doc, CHARTS / "detection_metrics_bar.png",
              caption="Chart 6 — Peak best-epoch metrics comparison")

    add_table(doc,
              ["Metric", "Fine-tune lần 1", "Fine-tune lần 2 (Improved)", "Δ"],
              [
                  ["Precision", f"{bl_p['P']:.4f}", f"{im_p['P']:.4f}", f"{pct(im_p['P'], bl_p['P']):+.2f}%"],
                  ["Recall", f"{bl_p['R']:.4f}", f"{im_p['R']:.4f}", f"{pct(im_p['R'], bl_p['R']):+.2f}%"],
                  ["mAP@0.5", f"{bl_p['mAP50']:.4f}", f"{im_p['mAP50']:.4f}", f"{pct(im_p['mAP50'], bl_p['mAP50']):+.2f}%"],
                  ["mAP@0.5:0.95", f"{bl_p['mAP50_95']:.4f}", f"{im_p['mAP50_95']:.4f}",
                   f"{pct(im_p['mAP50_95'], bl_p['mAP50_95']):+.2f}%"],
              ])

    # ================== 5. COUNTING QUALITY ==================
    add_heading(doc, "5. Kết quả counting quality (task-level)", 1)
    add_para(doc,
             "Video test: demo_traffic.mp4 — 178 frames, 5.9 giây, "
             "độ phân giải 1764x948, cảnh giao thông Cần Thơ nhìn từ trên xuống.")
    add_para(doc,
             f"Ground truth (đếm thủ công): {gt.get('motorcycle', 0)} motorcycle, "
             f"{gt.get('car', 0)} car, {gt.get('bus', 0)} bus, {gt.get('truck', 0)} truck "
             f"⇒ TỔNG {sum(gt.values())} xe.", bold=True)

    add_heading(doc, "5.1 So sánh counting per class", 2)
    add_image(doc, CHARTS / "counting_grouped.png", width_cm=16,
              caption="Chart 7 — Counting per class (màu = class, hatch = pipeline)")

    rows = []
    for cls in CLASS_ORDER:
        rows.append([
            cls,
            str(gt.get(cls, 0)),
            str(bl_c["pred"].get(cls, 0)),
            str(im_c["pred"].get(cls, 0)),
            str(bl_c["report"]["per_class"][cls]["abs_err"]),
            str(im_c["report"]["per_class"][cls]["abs_err"]),
        ])
    rows.append(["TỔNG", str(sum(gt.values())),
                 str(bl_c["report"]["total_pred"]),
                 str(im_c["report"]["total_pred"]),
                 "—", "—"])
    add_table(doc,
              ["Class", "GT", "Baseline pred", "Improved pred", "BL abs err", "IM abs err"],
              rows)

    add_heading(doc, "5.2 Tốc độ + accuracy tổng", 2)
    add_image(doc, CHARTS / "speed_accuracy.png", width_cm=16,
              caption="Chart 8 — FPS vs Accuracy trên demo video")

    add_table(doc,
              ["Chỉ số", "Baseline (COCO)", "Improved (fine-tune)"],
              [
                  ["Runtime", f"{bl_c['runtime_sec']:.2f}s", f"{im_c['runtime_sec']:.2f}s"],
                  ["FPS", f"{bl_c['fps']:.1f}", f"{im_c['fps']:.1f} ({speedup:.2f}x nhanh hơn)"],
                  ["Total pred", str(bl_c["report"]["total_pred"]), str(im_c["report"]["total_pred"])],
                  ["MAE", f"{bl_c['report']['MAE']:.2f}", f"{im_c['report']['MAE']:.2f}"],
                  ["MAPE (%)", f"{bl_c['report']['MAPE_percent']:.2f}", f"{im_c['report']['MAPE_percent']:.2f}"],
                  ["Overall accuracy", f"{bl_c['report']['overall_accuracy']*100:.2f}%",
                   f"{im_c['report']['overall_accuracy']*100:.2f}%"],
              ])

    add_para(doc, "Phân tích thẳng thắn:", bold=True)
    add_bullets(doc, [
        f"Improved nhanh hơn {speedup:.2f}x — do output 4 class thay vì 80 ⇒ head Detect nhẹ hơn, NMS ít candidate.",
        "Baseline under-count (71 vs 87 GT) — bỏ sót nhiều car do COCO ít quen camera góc cao VN.",
        f"Improved over-count ({im_c['report']['total_pred']} vs 87 GT) — có xu hướng tách 1 xe thành nhiều "
        "detection ở gần line đếm.",
        "Cả 2 accuracy tổng gần bằng — vì demo video không có motorcycle ⇒ lợi thế lớn nhất của Improved "
        "không được showcase ở đây.",
    ])
    add_para(doc, "Hạn chế đánh giá: Video demo chỉ 5.9 giây và có 0 xe máy trong GT ⇒ không phản ánh đủ "
                  "điểm mạnh Improved. Cần test thêm video có xe máy.", italic=True)

    # ================== 6. KẾT LUẬN ==================
    add_heading(doc, "6. Kết luận", 1)

    add_heading(doc, "6.1 Đóng góp chính", 2)
    add_bullets(doc, [
        "Xây dựng pipeline end-to-end: detect → track (ByteTrack) → count (line crossing) → visualize.",
        "Hợp nhất 3 dataset khác schema thành 1 tập 137k ảnh chuẩn 4-lớp (có class remapping).",
        "2 vòng fine-tune trên cùng kiến trúc YOLOv8s — kiến trúc không đổi, chỉ dữ liệu + LR khác.",
        "Boost xe máy đạt mAP@0.5 = 0.949 (đứng đầu 4 class) — chứng minh chiến lược data augmentation domain-specific có hiệu quả.",
        "GUI Streamlit hỗ trợ chọn model + xem kết quả.",
    ])

    add_heading(doc, "6.2 Bảng chốt cho slide", 2)
    add_table(doc,
              ["Chỉ số", "Baseline (COCO)", "Improved (fine-tune)", "Lợi thế"],
              [
                  ["Dataset train", "0 ảnh", "137k ảnh VN", "⭐ Improved"],
                  ["Số lớp output", "80 (filter 4)", "4 chuyên biệt", "⭐ Improved"],
                  ["mAP@0.5 (val)", "không đo", "0.850", "⭐ Improved"],
                  ["Motorcycle mAP", "không đo", "0.949", "⭐ Improved"],
                  ["FPS demo", "40.7", f"72.7 (nhanh {speedup:.2f}x)", "⭐ Improved"],
                  ["Params", "11.2M", "11.2M", "="],
                  ["Kiến trúc", "YOLOv8s", "YOLOv8s", "="],
              ])

    add_heading(doc, "6.3 Bài học rút ra", 2)
    add_bullets(doc, [
        '"Same model, better data → better result" — không cần model lớn hơn để cải thiện.',
        "Class remapping khi merge dataset là bước dễ sai — verify từ Roboflow UI trước khi tin.",
        "Continual fine-tune với LR thấp (0.001) an toàn hơn re-train from scratch cho dataset nhỏ.",
        "Metric val ≠ metric task — mAP tốt không tự động đồng nghĩa counting tốt (còn phụ thuộc tracker, line logic).",
    ])

    add_heading(doc, "6.4 Hạn chế & hướng phát triển", 2)
    add_para(doc, "Hạn chế hiện tại:", bold=True)
    add_bullets(doc, [
        "Motorcycle vẫn chỉ 0.85% bbox train ⇒ mAP50-95 = 0.609 (thấp hơn class khác).",
        "Truck confusion cao (van↔truck) do UA-DETRAC gộp.",
        "Demo video quá ngắn để đánh giá counting đầy đủ.",
    ])
    add_para(doc, "Đề xuất mở rộng:", bold=True)
    add_bullets(doc, [
        "Test trên nhiều video VN dài hơn (5-10 phút).",
        "Thử imgsz 640/768 (tăng khả năng bắt xe máy nhỏ ở xa).",
        "Áp dụng class-weighted sampling hoặc focal loss để giảm imbalance.",
        "Deploy trên edge device (Jetson) test real-time.",
    ])

    # ================== 7. GHI CHÚ KỸ THUẬT ==================
    add_heading(doc, "7. Ghi chú kỹ thuật", 1)
    add_bullets(doc, [
        "Class remapping vnv3: {0:1, 1:0, 2:3, 3:2} — script scripts/import_vnv3.py.",
        "Chỉ merge vào train, giữ val/test cũ để so sánh mAP công bằng.",
        "Best checkpoint tự cập nhật vào runs/.../weights/best.pt mỗi khi val mAP đạt đỉnh.",
        "Continual fine-tune với lr0=0.001 (default 0.01) — quan trọng để không phá kiến thức cũ.",
        "Eval config: conf=0.3, iou=0.5, imgsz=640, FP16, tracker=ByteTrack.",
    ])

    add_heading(doc, "8. File & artifact liên quan", 1)
    add_table(doc,
              ["Loại", "Đường dẫn"],
              [
                  ["Notebook báo cáo", "notebooks/report_baseline_vs_improved.ipynb"],
                  ["Script sinh báo cáo Word", "scripts/gen_report_docx.py"],
                  ["Script sinh chart + markdown", "scripts/gen_comparison_report.py"],
                  ["Script eval counting", "scripts/eval_counting_2pipelines.py"],
                  ["Kết quả eval JSON", "results/tables/eval_counting_2pipelines.json"],
                  ["Trọng số Improved", "runs/detect/runs/detect/train_v8s_ft_vnv3/weights/best.pt"],
                  ["Trọng số Baseline", "weights/yolov8s.pt"],
                  ["Config data", "data/data.yaml"],
              ])

    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUT)
    size_kb = OUT.stat().st_size / 1024
    print(f"[save] {OUT} ({size_kb:.1f} KB)")


if __name__ == "__main__":
    main()
