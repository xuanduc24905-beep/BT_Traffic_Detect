"""Sinh docs/NOI_DUNG_PPT.docx — nội dung chi tiết cho PPT.

Trong tam: giai thich baseline sao cho ai cung hieu (khong dung jargon),
va so sanh baseline vs nang cao ro rang, co so lieu cu the.

Moi 'slide' co:
- Tieu de
- Noi dung tren slide (bullet points ngan gon)
- Ghi chu thuyet trinh (day day du de doc them 30-60s)
- Goi y trinh chieu (hinh anh/bang)

Chay: python scripts/gen_ppt_content.py
"""
from pathlib import Path
from docx import Document
from docx.shared import Pt, RGBColor, Inches, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement


OUT = Path("docs/NOI_DUNG_PPT.docx")
OUT.parent.mkdir(parents=True, exist_ok=True)


def set_font(run, name="Times New Roman", size=12, bold=False, italic=False, color=None):
    run.font.name = name
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic
    if color:
        run.font.color.rgb = color
    rPr = run._element.get_or_add_rPr()
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts")
        rPr.append(rFonts)
    rFonts.set(qn("w:ascii"), name)
    rFonts.set(qn("w:hAnsi"), name)
    rFonts.set(qn("w:cs"), name)


def add_slide(doc, num, title, on_slide, speaker_notes, tips=None):
    """Add mot 'slide' vao doc gom: header, noi dung slide, ghi chu thuyet trinh, tip."""
    # Slide header
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(18)
    p.paragraph_format.keep_with_next = True
    r = p.add_run(f"SLIDE {num}. {title}")
    set_font(r, size=15, bold=True, color=RGBColor(0x1F, 0x4E, 0x79))

    # Bang: cot 1 = noi dung tren slide, cot 2 = ghi chu thuyet trinh
    table = doc.add_table(rows=1, cols=2)
    table.style = "Light Grid Accent 1"
    table.autofit = False
    table.columns[0].width = Inches(3.2)
    table.columns[1].width = Inches(3.5)

    # Header
    hdr = table.rows[0].cells
    for i, h in enumerate(["NOI DUNG TREN SLIDE", "GHI CHU THUYET TRINH (doc mieng)"]):
        hdr[i].text = ""
        p = hdr[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(h)
        set_font(r, size=10, bold=True, color=RGBColor(0xFF, 0xFF, 0xFF))
        tcPr = hdr[i]._element.get_or_add_tcPr()
        shd = OxmlElement("w:shd")
        shd.set(qn("w:val"), "clear")
        shd.set(qn("w:fill"), "1F4E79")
        tcPr.append(shd)

    # Data row
    row = table.add_row().cells

    # Cot 1: bullet on slide
    c1 = row[0]
    c1.text = ""
    for item in on_slide:
        p = c1.add_paragraph()
        p.paragraph_format.left_indent = Cm(0.3)
        p.paragraph_format.first_line_indent = Cm(-0.3)
        r = p.add_run(f"- {item}")
        set_font(r, size=11)

    # Cot 2: speaker notes
    c2 = row[1]
    c2.text = ""
    p = c2.paragraphs[0]
    r = p.add_run(speaker_notes)
    set_font(r, size=11)

    # Tip design
    if tips:
        p = doc.add_paragraph()
        r = p.add_run(f"[Goi y trinh chieu]: {tips}")
        set_font(r, size=10, italic=True, color=RGBColor(0x80, 0x40, 0x00))


def add_h(doc, text, level=1):
    sizes = {0: 20, 1: 16, 2: 13}
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(14)
    p.paragraph_format.space_after = Pt(6)
    r = p.add_run(text)
    set_font(r, size=sizes.get(level, 13), bold=True)
    if level == 0:
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    return p


def main():
    doc = Document()

    # ========== COVER ==========
    add_h(doc, "NOI DUNG CHI TIET PPT THUYET TRINH", level=0)
    add_h(doc, "Chu de 10 - Dem va Phan loai Phuong tien Giao thong", level=1)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("Tai lieu huong dan tao slide PowerPoint (17 slide)")
    set_font(r, size=13, italic=True)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("Trong tam: Giai thich baseline sao cho nguoi khong chuyen tech cung hieu, "
                  "va so sanh ro rang giua baseline vs nang cao.")
    set_font(r, size=11, italic=True, color=RGBColor(0x66, 0x66, 0x66))

    # Guide
    add_h(doc, "Cach dung tai lieu nay", level=2)
    for x in [
        "Moi 'slide' co 2 cot: noi dung tren slide (chu it) + ghi chu thuyet trinh (doc mieng).",
        "Copy noi dung cot trai vao PowerPoint. Cot phai la kich ban thuyet trinh.",
        "Goi y trinh chieu ben duoi noi hinh anh/bang nao nen chen.",
        "Doi ten trinh chieu tuong ung voi thanh vien phu trach de tap thuyet trinh.",
    ]:
        p = doc.add_paragraph(style="List Bullet")
        r = p.add_run(x)
        set_font(r, size=11)

    doc.add_page_break()

    # ==============================================================
    # ================ 17 SLIDES ===================================
    # ==============================================================

    # ---------- SLIDE 1: BIA ----------
    add_slide(doc, 1,
        title="Bia - Gioi thieu nhom & de tai",
        on_slide=[
            "TEN DE TAI: He thong dem va phan loai phuong tien giao thong qua camera giam sat",
            "Chu de 10 - Bai tap lon Computer Vision",
            "Giao vien huong dan: [dien ten]",
            "Nhom sinh vien: [dien ten 4 nguoi]",
            "Lop: [dien lop]",
            "Ngay bao cao: [dien ngay]",
        ],
        speaker_notes=(
            "Chao thay/co va cac ban. Nhom em xin trinh bay bai tap lon Chu de 10: "
            "xay dung he thong dem va phan loai phuong tien giao thong bang camera giam sat. "
            "Em ten la [ten nguoi thuyet trinh dau tien] - dai dien nhom [ten nhom]. "
            "Bai thuyet trinh cua nhom em keo dai khoang 15-20 phut, chia thanh 4 phan chinh, "
            "moi thanh vien phu trach 1 phan. Bat dau nhe."
        ),
        tips="Design don gian, mau chu do thanh chu, chen logo truong.")

    # ---------- SLIDE 2: BAI TOAN ----------
    add_slide(doc, 2,
        title="Bai toan thuc te: dem xe kho nhu the nao?",
        on_slide=[
            "Giao thong Viet Nam: mat do phuong tien cao, un tac thuong xuyen",
            "Can dem chinh xac de: quy hoach den giao thong, dieu tiet lan xe, khao sat luu luong",
            "Cach lam thu cong: nguoi ngoi coi video/dung ngoai duong dem tay",
            "Van de: tot nhieu nguoi + de sai + khong lam realtime duoc",
            "GIAI PHAP: he thong dem xe tu dong bang camera + AI",
        ],
        speaker_notes=(
            "Truoc khi noi cong nghe, em muon dat van de tu doi thuc. Giao thong Viet Nam, "
            "dac biet o cac thanh pho lon, ai cung biet la mat do xe rat cao va un tac lien tuc. "
            "De giai quyet van de nay, cac co quan quan ly can du lieu chinh xac ve luu luong xe "
            "de quy hoach den giao thong, phan bo lan xe, hoac to chuc phan luong. "
            "Truoc day, viec dem xe thuong lam thu cong: cu phai co nguoi ngoi coi video hoac dung "
            "ngoai duong dem bang tay. Cach nay ton nhieu nhan luc, de sai sot vi met moi, va "
            "khong the lam duoc realtime tren nhieu ngua duong cung luc. "
            "Vi vay muc tieu de tai la xay dung 1 he thong TU DONG dem xe qua camera, chinh xac va "
            "chay realtime, giup thay the cong doan dem tay day co dien."
        ),
        tips="Chen 1 anh un tac giao thong VN + 1 anh nguoi dem xe thu cong ben canh nhau.")

    # ---------- SLIDE 3: PIPELINE TONG QUAN ----------
    add_slide(doc, 3,
        title="Y tuong giai quyet: pipeline 3 buoc",
        on_slide=[
            "BUOC 1 - PHAT HIEN (Detection): AI nhin vao anh, khoanh vung xe co trong anh",
            "BUOC 2 - THEO DOI (Tracking): dan nhan ID cho tung xe, giu ID xuyen suot cac frame",
            "BUOC 3 - DEM (Counting): ve 1 duong ke ao, xe nao di qua duong thi dem 1 lan",
            "Ket qua: video co so dem hien truc tiep + bang thong ke ket qua",
        ],
        speaker_notes=(
            "He thong cua nhom em hoat dong qua 3 buoc rat don gian. "
            "Buoc 1 la PHAT HIEN: cu moi frame video, mo hinh AI se nhin vao anh va khoanh "
            "vung tat ca cac xe co trong anh - giong nhu ban tro nen dua ban tay chi vao tung xe. "
            "Buoc 2 la THEO DOI: mo hinh se dan cho moi xe 1 con so ID rieng, va giu con so nay "
            "xuyen suot cac frame - de biet chiec xe frame nay va chiec xe frame sau la CUNG 1 xe "
            "hay 2 xe khac nhau. "
            "Buoc 3 la DEM: nhom em ve 1 duong ke ao tren frame, moi khi 1 xe co ID duy nhat di qua "
            "duong ke thi tang bien dem len 1. Nho co ID nen 1 xe chi dem duoc 1 lan, khong bi dem trung. "
            "Cuoi cung xuat ra video co bang dem hien truc tiep, va CSV/bieu do thong ke."
        ),
        tips="Chen so do 3 buoc voi mui ten. Moi buoc co 1 icon: mat, ID number, duong ke.")

    # ---------- SLIDE 4: BASELINE LA GI ----------
    add_slide(doc, 4,
        title="'Baseline' nghia la gi?",
        on_slide=[
            "BASELINE = phien ban co ban nhat, don gian nhat de bat dau",
            "Vi du: nau com. Baseline = com trang. Nang cao = com chien tom xa xiu.",
            "Trong hoc may (Machine Learning), baseline la mo hinh don gian nhat co the chay duoc",
            "Ta phai co baseline de: (1) co diem mo neo so sanh, (2) chung minh cai tien co dang gia khong",
            "Neu 'baseline da chay 24% chinh xac' -> ta biet phai lam gi de nang len 90-99%",
        ],
        speaker_notes=(
            "Trong slide tiep theo, em se dung nhieu tu 'baseline' nen em muon giai thich truoc. "
            "Baseline la mot khai niem quan trong trong nghien cuu va bai tap AI - no la 'phien ban co ban nhat, "
            "don gian nhat'. Vi du de hieu: neu ta thi nau com, baseline se la 'com trang thuong', con "
            "phien ban nang cao la 'com chien tom xa xiu'. Cai baseline khong ngon nhung phai co, de ta so ra "
            "duoc mon nang cao thuc su ngon hon. "
            "Trong bai tap nay, baseline la mo hinh AI co ban - dung nhung thu san co, khong tinh chinh gi. "
            "Neu baseline dat 24% chinh xac, va sau khi cai tien ta dat 99%, thi ta chung minh duoc "
            "phan cai tien LAM RA su khac biet that su - khong phai chi may man. "
            "Do la tam quan trong cua baseline: la moc de so sanh, de danh gia cong sut."
        ),
        tips="Chen anh 'com trang vs com chien' de an tuong. Hoac slider 24% vs 99%.")

    # ---------- SLIDE 5: BASELINE CU THE ----------
    add_slide(doc, 5,
        title="Baseline cua chu de 10 la gi? (code giao vien cung cap)",
        on_slide=[
            "File 10_traffic_counting.py - do giao vien cung cap",
            "Su dung yolov8n.pt: mot AI da duoc train truoc tren tap COCO (80 loai vat)",
            "Ghi chu: khong can train gi, chi CHAY luon la co ket qua",
            "Ve 1 duong ke ngang giua frame + dem xe di qua",
            "Muc dich: cho sinh vien HIEU pipeline co ban truoc khi TU CAI TIEN",
            "Yeu cau cua thay/co: MO RONG baseline nay, khong duoc nop nguyen ban",
        ],
        speaker_notes=(
            "Cu the trong bai tap chu de 10, thay/co da cung cap cho sinh vien 1 file code goi la "
            "10_traffic_counting.py. Do la baseline. File nay lam gi? "
            "No dung mot mo hinh AI ten la yolov8n.pt - day la 1 mo hinh da duoc train truoc boi cong ty "
            "Ultralytics tren mot tap du lieu ten la COCO. COCO co 80 loai vat, tu nguoi, cho, meo, den "
            "xe hoi, xe may, xe khach... "
            "Cai dac biet la mo hinh nay khong can train gi ca, chi tai ve va chay la co the phat hien "
            "duoc cac loai xe. Rat tien loi. "
            "File baseline nay ve 1 duong ke ao ngang giua frame video, va moi khi 1 chiec xe di tu tren "
            "xuong qua duong nay, no se dem +1 vao loai xe do. "
            "Y do thay/co la muon sinh vien HIEU cach pipeline hoat dong co ban truoc, sau do BAT BUOC "
            "phai TU cai tien, khong duoc nop nguyen file baseline vi qua don gian."
        ),
        tips="Chen screenshot code baseline (10 dong dau) + so do 1 duong ke ngang.")

    # ---------- SLIDE 6: BASELINE HOAT DONG ----------
    add_slide(doc, 6,
        title="Baseline hoat dong nhu the nao? (giai thich chi tiet)",
        on_slide=[
            "1. Doc video tung frame (30 anh/giay)",
            "2. Voi moi frame: goi model.track() -> nhan lai danh sach xe + ID",
            "3. Voi moi xe: tinh tam Y cua khung bao (giua thanh doc)",
            "4. Neu tam Y frame truoc < line_y, tam Y hien tai >= line_y",
            "   -> xe da di tu tren xuong qua line -> DEM +1 cho loai xe do",
            "5. Ghi nho ID da dem vao counted_ids -> khong dem lai lan 2",
            "6. Ket thuc: xuat bieu do bar chart va in ket qua",
        ],
        speaker_notes=(
            "Em giai thich chi tiet hon cach baseline chay. "
            "Video la 1 chuoi cac buc anh chieu voi toc do 30 anh moi giay. Baseline doc tung anh mot. "
            "Voi moi anh, goi ham model.track() - ham nay lam 2 viec cung luc: phat hien xe VA gan cho moi "
            "xe 1 con so ID. "
            "Voi moi xe co trong anh, ta tinh 'tam Y' cua khung chu nhat bao quanh xe - do la diem "
            "chinh giua theo chieu doc. "
            "Bay gio thu thuat la: neu tam Y cua xe do o frame TRUOC nam TREN duong ke, va o frame HIEN "
            "TAI nam DUOI duong ke - nghia la xe da vua di qua duong tu tren xuong. Ta se dem +1 cho loai "
            "xe do (xe con hay xe khach...). "
            "Diem quan trong: ta luu ID cua nhung xe da dem vao 1 tap hop counted_ids. Neu xe do sau nay "
            "quay lai qua line lan 2, ta kiem tra ID trong counted_ids va bo qua - khong dem trung. "
            "Cuoi cung, ta xuat bang thong ke va bieu do cot don gian."
        ),
        tips="Chen so do 4-5 frame lien tiep voi tam Y giam dan qua line. Highlight moment 'CUT'.")

    # ---------- SLIDE 7: BASELINE - KET QUA ----------
    add_slide(doc, 7,
        title="Ket qua thuc te cua baseline (chay tren video test)",
        on_slide=[
            "Video test: demo_traffic.mp4 (5.9 giay, 178 frame, GT = 87 xe)",
            "Ket qua baseline (yolov8n COCO): dem duoc 21/87 xe -> chi 24% chinh xac",
            "Chi tiet: 19 xe con + 2 xe khach. THIEU 66 xe khac (chua noi den van)",
            "Ket qua kem vi:",
            "  - Model yolov8n qua nho (3 trieu tham so), khong tinh chi tiet",
            "  - Model duoc train tren anh COCO (Internet), khong quen anh camera giao thong",
            "  - Chi co 1 duong ke ngang -> xe di ngang khong duoc dem",
            "  - Nguong confidence 0.4 kha cao -> bo qua nhieu xe mo ho",
        ],
        speaker_notes=(
            "Bay gio la phan quan trong: xem baseline thuc su chay tot khong. "
            "Nhom em test tren 1 doan video demo dai 5.9 giay, gom 178 frame. Nhom em da dem tay ground truth "
            "trong video co 87 xe tong cong. "
            "Ket qua baseline: chi dem duoc 21/87 xe, chinh xac 24%. Rat kem. Cu the la 19 xe con + 2 xe khach, "
            "hoan toan bo qua 66 xe con lai. "
            "Vi sao lai kem the? Co 4 ly do chinh: "
            "1) Model yolov8n co kich thuoc rat nho, chi 3 trieu tham so - nen khong tinh vi lam. "
            "2) Model duoc train tren tap COCO chua nhieu anh tu Internet, khong phai anh camera giao thong. "
            "Khi gap goc quay camera cao va nhieu xe chen chuc, model bi 'la nuoc' va bo lo. "
            "3) Baseline chi co 1 duong ke ngang giua frame - nhung 1 so xe di sang phai/trai khong qua duong "
            "nay -> khong duoc dem. "
            "4) Nguong confidence 0.4 la kha nghiem khac - bo qua nhung xe khong tu tin cao, dan den miss nhieu. "
            "Voi 24% chinh xac, baseline hoan toan khong dung duoc cho ung dung thuc te - can nang cap."
        ),
        tips="Chen bieu do baseline traffic_stats.png (co san o baseline/) + bang GT vs Pred.")

    # ---------- SLIDE 8: TAI SAO CAN CAI TIEN ----------
    add_slide(doc, 8,
        title="Tai sao can cai tien? 4 van de cua baseline",
        on_slide=[
            "Van de 1: MODEL QUA NHO -> nang cap len yolov8s (11 trieu tham so)",
            "Van de 2: TRAIN TREN COCO -> fine-tune lai tren du lieu giao thong (UA-DETRAC + Viet Nam)",
            "Van de 3: 1 DUONG KE -> them nhieu duong + phan chieu di (ltr/rtl)",
            "Van de 4: BASELINE KHONG CO XE MAY -> them dataset Viet Nam co xe may",
            "5 CAI TIEN LON cua nhom -> nang tu 24% len 99% chinh xac",
        ],
        speaker_notes=(
            "Sau khi thay baseline chi dat 24%, nhom em xac dinh 4 van de chinh cua baseline. "
            "Van de 1: model qua nho. Giai phap: nang cap tu yolov8n (3M tham so) len yolov8s (11M tham so). "
            "yolov8s to gap 4 lan, tinh chi tiet hon nhung van chay nhanh. "
            "Van de 2: model duoc train tren du lieu COCO chung chung, khong quen giao thong. Giai phap: "
            "fine-tune - tuc la lay yolov8s pretrained roi 'day' them cho no biet xe giao thong bang cach "
            "dua vao xem hang tram nghin anh giao thong. Nhom em dung 2 dataset: UA-DETRAC (68k anh xe hop) "
            "va Vietnam CanTho (674 anh giao thong VN). "
            "Van de 3: chi co 1 duong ke doc lap. Giai phap: cho phep dat NHIEU duong ke, va phan biet chieu "
            "xe di - trai qua phai hay phai qua trai - de ung dung dem xe VAO/RA khu vuc. "
            "Van de 4 - quan trong nhat cho Viet Nam: baseline khong biet detect xe may. UA-DETRAC toan xe hop, "
            "khong co xe may. Giai phap: bo sung dataset Viet Nam CanTho co xe may -> merge chung lai. "
            "Voi 5 cai tien lon nay (them 1 nua la UI Streamlit), do chinh xac nang tu 24% len 99% - gap "
            "4 lan."
        ),
        tips="Chen bang '4 van de - 4 giai phap' voi mui ten sang phai. Hoac bar chart 24% vs 99%.")

    # ---------- SLIDE 9: NANG CAP 1 - MODEL TO HON ----------
    add_slide(doc, 9,
        title="Nang cap 1: Model to hon (yolov8n -> yolov8s)",
        on_slide=[
            "yolov8n = nano (3 trieu tham so, kich thuoc 6MB)",
            "yolov8s = small (11 trieu tham so, kich thuoc 22MB) - to gap 3.7 lan",
            "V dau la kich thuoc model - so lop mang than kinh + so tham so",
            "Model to hon = tinh chi tiet hon = bat duoc xe nho, xe che khuat mot phan",
            "Danh doi: cham hon mot chut, ton VRAM hon - nhung van chay realtime duoc",
        ],
        speaker_notes=(
            "Nang cap dau tien la doi model. YOLOv8 co 5 kich co: n (nano), s (small), m (medium), l (large), "
            "x (extra large). Baseline dung nano - nho nhat, chi 3 trieu tham so. "
            "Nhom em nang len small - 11 trieu tham so, to gap 3.7 lan. Voi so tham so nhieu hon, model "
            "co the hoc duoc nhieu chi tiet phuc tap hon - bat duoc nhung chiec xe nho, xe che khuat mot phan, "
            "xe o xa camera. "
            "Danh doi la: cham hon 1 chut trong inference, ton VRAM (bo nho GPU) hon. Nhung tren GPU RTX 3500 "
            "12GB cua chung em van chay duoc realtime tren 30 FPS - dap ung tot cho ung dung camera. "
            "Vi sao khong chon medium hay large? Vi train medium mat 12-15h, large mat >24h. Small la diem can "
            "bang tot nhat giua chat luong va thoi gian train."
        ),
        tips="Chen bang so sanh 5 bien the YOLOv8 (params, mAP, speed). Highlight cot 's'.")

    # ---------- SLIDE 10: NANG CAP 2 - DATASET VN ----------
    add_slide(doc, 10,
        title="Nang cap 2: Them dataset Viet Nam co xe may",
        on_slide=[
            "UA-DETRAC (Trung Quoc): 68k anh highway - toan xe hop, KHONG CO xe may",
            "Vietnam CanTho (Roboflow): 674 anh duong pho Can Tho - CO xe may Viet Nam",
            "Merge 2 dataset: chuyen ve chung 1 schema 4 lop: {xe may, xe con, xe khach, xe tai}",
            "Ket qua sau merge: 68,547 anh train + 14,344 anh val + 56,381 anh test",
            "Diem quan trong: co 2004 xe may de model hoc - moc du 4-8% cua dataset nhung du de bat duoc",
        ],
        speaker_notes=(
            "Nang cap thu 2, va la quan trong nhat cho topic Viet Nam: giai quyet van de 'khong co xe may'. "
            "UA-DETRAC la mot dataset lon, 68 nghin anh, nhung no la anh cao toc Trung Quoc - chi co xe hop, "
            "xe khach, xe tai. Khong co 1 chiec xe may nao. Do la ly do baseline khong biet detect xe may. "
            "Nhom em phai tim mot dataset khac co xe may. Sau khi tim kiem, nhom em thay dataset Vietnam CanTho "
            "tren Roboflow - 674 anh chup duong pho Can Tho, co day du xe may, xe hop, xe khach, xe tai. "
            "Vi 2 dataset co cach dat ten class khac nhau, nhom em phai 'merge' - chuyen chung ve chung 1 schema "
            "4 lop: xe may, xe con, xe khach, xe tai. "
            "Sau khi merge, tap huan luyen co 68 nghin anh, tap val 14 nghin, tap test 56 nghin. Trong do co "
            "2004 xe may - chi khoang 0.4% cua tap huan luyen. Nghe co ve it, nhung du de model hoc duoc 'hinh "
            "dang xe may la nhu the nao', va sau training model dat mAP xe may = 0.87 - rat cao."
        ),
        tips="Chen 2 anh side-by-side: 1 anh UA-DETRAC highway TQ + 1 anh CanTho co xe may.")

    # ---------- SLIDE 11: NANG CAP 3 - FINE-TUNE ----------
    add_slide(doc, 11,
        title="Nang cap 3: Fine-tune yolov8s tren merged dataset",
        on_slide=[
            "Fine-tune = day them cho model bang du lieu moi (khong train tu dau)",
            "Vi du: yolov8s da biet 'xe hoi la gi' tu COCO. Ta chi day them 'xe may Viet Nam trong the nay'",
            "Cau hinh training: 50 epoch, batch 32, imgsz 512, cache RAM",
            "Phan cung: GPU RTX 3500 Ada 12GB (laptop). Thoi gian: 5 gio 30 phut",
            "Ket qua: mAP@0.5 dat 0.843 tren tap test 56k anh - cai thien manh so voi baseline",
        ],
        speaker_notes=(
            "Nang cap thu 3 la fine-tune. Fine-tune nghia la 'day them' - lay model yolov8s da biet nhieu thu "
            "tu tap COCO, roi 'day them' cho no biet ve giao thong bang du lieu merged cua nhom. "
            "Vi du de hieu: yolov8s pretrained da biet 'xe hoi' tu tap COCO. Nhom em chi can day them "
            "'xe may Viet Nam trong nhu the nay, xe con hop chu nhat, goc quay camera cao...'. Model khong "
            "hoc lai tu dau ma cham vao kien thuc san co roi tinh chinh - nhanh va hieu qua hon nhieu. "
            "Cau hinh training: 50 epoch (moi epoch = duyet toan bo 68k anh 1 lan), batch size 32 (moi lan tinh "
            "toan 32 anh), image size 512 (thu nho anh xuong 512x512 truoc khi dua vao model - nhanh hon 640). "
            "Cache dataset vao RAM 20GB - khoi phai doc dia lien tuc. "
            "Phan cung: laptop cua Duc dung GPU RTX 3500 Ada 12GB. Thoi gian training: 5 gio 30 phut. Chay qua "
            "dem la sang co ket qua. "
            "Ket qua sau training: mAP@0.5 = 0.843 - do chinh xac cao tren tap test 56 nghin anh."
        ),
        tips="Chen bieu do loss + mAP theo epoch (results.png tu training_report). Highlight epoch cuoi.")

    # ---------- SLIDE 12: NANG CAP 4 - DIRECTION ----------
    add_slide(doc, 12,
        title="Nang cap 4: Dem theo huong di (direction counting)",
        on_slide=[
            "Baseline: 1 duong ke, ai qua cung dem +1 - khong biet vao hay ra",
            "Ung dung thuc te can biet CHIEU: bao nhieu xe VAO khu vuc, bao nhieu xe RA",
            "Giai phap: cross-product giua vector duong ke va vector di chuyen cua xe",
            "cross > 0 -> xe di tu trai sang phai (ltr - left to right)",
            "cross < 0 -> xe di tu phai sang trai (rtl - right to left)",
            "Cho phep cau hinh: 'both' (dem ca 2 chieu), 'ltr' (chi 1 chieu), 'rtl'",
        ],
        speaker_notes=(
            "Nang cap thu 4 la dem theo huong di. Baseline chi co 1 duong ke, ai qua cung dem +1 - khong biet "
            "xe do di vao khu vuc hay di ra. Nhung ung dung thuc te thuong can biet chieu: vi du 'sang nay co "
            "500 xe DI VAO cong so, chieu ve 480 xe DI RA'. Nhu vay moi lam duoc bao cao co y nghia. "
            "Giai phap ky thuat: dung 'cross-product' - phep tinh trong hinh hoc. Ta co 2 vector: vector cua "
            "duong ke (tu diem p1 den p2) va vector di chuyen cua xe (tu tam frame truoc den tam frame hien tai). "
            "Ta tinh cross-product cua 2 vector nay. Dau cua ket qua se cho biet xe di theo chieu nao so voi "
            "duong ke. Neu duong > 0, xe di tu trai qua phai theo chieu vector duong ke. Neu am, xe di nguoc lai. "
            "Nhom em goi 2 chieu la 'ltr' (left-to-right) va 'rtl' (right-to-left). Cho phep cau hinh 'both' de "
            "dem ca 2, hoac chi 1 chieu tuy ung dung. "
            "Vi du 1 sieu thi co the dat 2 line: 1 line chi dem xe vao bai xe, 1 line chi dem xe ra."
        ),
        tips="Chen so do vector duong ke + vector di chuyen + dau cross-product. Chieu mui ten.")

    # ---------- SLIDE 13: NANG CAP 5 - UI ----------
    add_slide(doc, 13,
        title="Nang cap 5: Web UI Streamlit (khong can code)",
        on_slide=[
            "Baseline chay qua terminal Python - nguoi khong code khong dung duoc",
            "Nhom em xay 1 web UI don gian bang Streamlit - mo trinh duyet la dung",
            "3 tab chinh:",
            "  - Tab 1: Upload video, chon model, dieu chinh nguong -> chay pipeline",
            "  - Tab 2: Xem thong ke chi tiet + bieu do (bar, cumulative, heatmap)",
            "  - Tab 3: Danh gia do chinh xac vs ground truth do minh dem tay",
            "Ung dung: nguoi khong biet code van co the su dung ket qua nhom lam ra",
        ],
        speaker_notes=(
            "Nang cap thu 5 lien quan den trai nghiem nguoi dung. Baseline chay qua dong lenh Python - chi lap "
            "trinh vien moi dung duoc. Nguoi khac nhu can bo giao thong hay quan ly chan chinh, khong biet code, "
            "khong dung duoc ket qua nhom em lam. "
            "Vi vay nhom em xay 1 giao dien web don gian bang Streamlit - framework Python cho phep tao web UI "
            "nhanh chong. Chi can mo trinh duyet la dung duoc, khong can cai dat gi phuc tap. "
            "Giao dien co 3 tab. Tab 1 la nga vao: upload video muon dem, chon model AI, dieu chinh nguong "
            "confidence, roi bam 'chay pipeline'. Sau vai giay se co ket qua video co counter hien truc tiep. "
            "Tab 2 la thong ke: bieu do cot theo loai xe, do thi cumulative theo thoi gian, heatmap thoi gian x "
            "loai xe, va bang chi tiet. "
            "Tab 3 la danh gia: nguoi dung co the tai len file ground truth do minh dem tay hoac dien so truc "
            "tiep, he thong se tinh do chinh xac accuracy, MAE, MAPE. "
            "Voi UI nay, ket qua cua nhom em thuc su co the ung dung duoc cho nguoi khong bay code."
        ),
        tips="Chen 3 screenshot cua 3 tab Streamlit + 1 anh screen phone/laptop dung UI.")

    # ---------- SLIDE 14: BANG SO SANH ----------
    add_slide(doc, 14,
        title="BANG SO SANH: baseline vs cac phien ban nang cao",
        on_slide=[
            "3 phien ban cung so sanh tren video demo 5.9 giay (GT = 87 xe):",
            "",
            "1. Baseline yolov8n COCO (starter code): 21/87 -> 24% chinh xac",
            "2. Baseline yolov8s COCO (giu starter code, chi doi model): 22/87 -> 25%",
            "3. Nhom (yolov8s fine-tune tren merged VN): 86/87 -> 99% chinh xac",
            "",
            "KET LUAN QUAN TRONG: doi tu n sang s KHONG giup nhieu (chi tu 21 len 22)",
            "Cai giup THUC SU la FINE-TUNE tren du lieu giao thong VN (+64 xe detect duoc)",
        ],
        speaker_notes=(
            "Day la slide quan trong nhat cua bai thuyet trinh. Nhom em so sanh 3 phien ban tren cung 1 video "
            "test dai 5.9 giay, ground truth co 87 xe. "
            "Phien ban 1: baseline yolov8n COCO - starter code cua thay/co. Dem duoc 21 xe, chinh xac 24%. "
            "Phien ban 2: van la starter code (khong doi gi), chi doi model tu yolov8n sang yolov8s. Dem duoc "
            "22 xe, chinh xac 25%. "
            "Phien ban 3: cua nhom - yolov8s duoc fine-tune tren merged VN dataset. Dem duoc 86 xe, chinh xac "
            "99%. "
            "Bay gio nhin cho ky: tu phien ban 1 sang 2, chi doi model tu nho sang to hon - chi cai thien duoc "
            "1 xe (21 sang 22). Nghia la 'chon model to hon' KHONG PHAI la giai phap. "
            "Cai thuc su giup la tu phien ban 2 sang 3: fine-tune tren VN data. Con so nhay tu 22 len 86 - CAI "
            "THIEN 64 xe. Day chinh la dong gop lon nhat cua nhom em. "
            "Neu ai do noi 'nhom em chi may man voi model to hon', nhom em chung minh duoc dieu do khong dung."
        ),
        tips="Bang so sanh 3 hang o giua slide, dung mau: 24% do, 25% cam, 99% xanh la. Bar chart phia duoi.")

    # ---------- SLIDE 15: METRICS CHI TIET ----------
    add_slide(doc, 15,
        title="Metrics chi tiet: mAP tren tap test 56k anh",
        on_slide=[
            "Ngoai counting, con danh gia detection quality bang mAP - chuan cua cong dong ML",
            "Tren tap test 56,381 anh co san label:",
            "  - mAP@0.5 tong: 0.843 (rat cao)",
            "  - Precision (do chinh xac cua predictions): 0.886",
            "  - Recall (ty le xe duoc phat hien): 0.777",
            "Chi tiet per-class:",
            "  - motorcycle: 0.871 (xuat sac - thanh cong lon)",
            "  - car: 0.744 - bus: 0.781 - truck: 0.524",
            "Truck yeu vi da gop 'van' cua UA-DETRAC vao 'truck' -> gay confusion",
        ],
        speaker_notes=(
            "Ngoai metric counting o slide truoc, nhom em cung danh gia model o muc do 'detection' bang metric "
            "chuan cua cong dong Machine Learning, goi la mAP - mean Average Precision. "
            "Metric nay do chat luong bounding box + phan loai class, tinh tren tap test 56 nghin anh co san label. "
            "Ket qua tong: mAP@0.5 = 0.843. Trong nghien cuu, mAP@0.5 tren 0.8 la muc rat cao. "
            "Precision 0.886 nghia la khi model noi 'day la xe', xac suat DUNG la 88.6%. Recall 0.777 nghia la "
            "trong tat ca xe co that trong anh, model bat duoc 77.7%. "
            "Xem chi tiet tung class: xe may dat mAP 0.871 - xuat sac. Day la thanh cong lon nhat cua nhom em vi "
            "chung minh viec merge dataset VN thuc su hieu qua. "
            "Xe con 0.744, xe khach 0.781 - deu tot. "
            "Chi co xe tai (truck) yeu hon: 0.524. Ly do la trong luc merge, nhom em da gom class 'van' cua "
            "UA-DETRAC vao class 'truck' (vi 'van' co hinh dang gan 'truck' nhat). Nhung 'van' va 'truck' van "
            "co su khac biet nen model bi nham lan mot phan. Do la trade-off nhom em chap nhan de co schema 4-class "
            "thong nhat."
        ),
        tips="Chen confusion matrix (docs/training_report/confusion_matrix.png) + PR curve.")

    # ---------- SLIDE 16: DEMO VIDEO ----------
    add_slide(doc, 16,
        title="Demo video + Streamlit UI",
        on_slide=[
            "Chieu video output co counter hien truc tiep",
            "Screenshot Streamlit UI: upload video -> nhan run -> xem ket qua",
            "Neu setup duoc: LIVE DEMO thay/co xem realtime",
            "Ket qua tren video khac (video canh 30s giao thong VN):",
            "  - Model detect duoc xe may, xe con, xe khach",
            "  - Bang thong ke bucket theo phut, heatmap thoi gian",
        ],
        speaker_notes=(
            "Bay gio nhom em xin phep chieu vai demo truc tiep. "
            "[Chieu video output co counter hien] - day la ket qua model chay tren video test demo_traffic.mp4. "
            "Cac ban co the thay: khung xanh la bounding box + track ID, duong do la counting line, so trang o "
            "goc tren la counter tich luy. Moi khi 1 xe di qua duong do, counter tang len 1. "
            "[Neu duoc, mo Streamlit UI]: bay gio em mo Streamlit. Upload 1 video, chon model yolov8s cua nhom, "
            "chinh nguong confidence, bam 'chay pipeline'. Sau 5-10 giay se co ket qua. "
            "Tab 'Thong ke': se hien bieu do so luong xe theo loai, cumulative theo thoi gian, va heatmap thoi "
            "gian x loai xe. "
            "Neu chuan bi truoc video giao thong VN dai hon (vd 30 giay hoac 1 phut), nhom em chieu de thay "
            "duoc kha nang detect xe may thuc te trong tinh huong Viet Nam."
        ),
        tips="Chuan bi truoc: 1 video output (baseline_out.mp4 hoac notebook out) + screenshot Streamlit UI.")

    # ---------- SLIDE 17: KET LUAN ----------
    add_slide(doc, 17,
        title="Ket luan + huong phat trien + Q&A",
        on_slide=[
            "DA HOAN THANH:",
            "  - Pipeline day du 6 yeu cau topic 10 (detect, track, count, thong ke, bieu do, eval)",
            "  - 5 nang cap chinh: model to hon, fine-tune, dataset VN, direction, UI",
            "  - Ket qua: 99% chinh xac tren video test, mAP 0.843, detect duoc xe may 0.87",
            "HAN CHE:",
            "  - Class truck con yeu (0.52) do trade-off van vs truck",
            "  - Chi test tren 1 video 5.9 giay - can them video dai hon",
            "HUONG PHAT TRIEN:",
            "  - Bo sung data VN (Ha Noi, TP.HCM, dem, mua)",
            "  - Deploy ONNX cho edge device (Jetson Nano)",
            "  - Realtime dashboard + alerting khi luu luong vuot nguong",
            "CAM ON THAY/CO va cac ban da lang nghe. Xin moi cau hoi (Q&A)",
        ],
        speaker_notes=(
            "Slide cuoi cung, em tong ket lai. "
            "Da hoan thanh: pipeline day du 6 yeu cau cua chu de 10, va bo sung 5 nang cap lon so voi baseline. "
            "Ket qua: 99% chinh xac tren video test, mAP tren tap test 56 nghin anh la 0.843, va dac biet detect "
            "duoc xe may voi mAP 0.87 - dieu ma baseline khong lam duoc. "
            "Han che: class xe tai con yeu do quyet dinh gom van vao truck, va nhom em chi test tren 1 video ngan. "
            "Neu co them thoi gian, nhom em muon test tren nhieu video giao thong VN thuc te hon. "
            "Huong phat trien tuong lai: 1) bo sung dataset VN da dang hon nhu Ha Noi, TP.HCM, quay dem, quay mua. "
            "2) Deploy model dang ONNX de chay tren edge device nhu Jetson Nano - phu hop cho camera giao thong "
            "thuc te. 3) Xay dung dashboard realtime co alerting khi luu luong vuot nguong. "
            "Nhom em xin cam on thay/co va cac ban da lang nghe. Xin moi cac cau hoi (Q&A)."
        ),
        tips="Slide chia 3 cot: DA HOAN THANH - HAN CHE - HUONG PHAT TRIEN. Cuoi cung: 'THANK YOU'.")

    doc.add_page_break()

    # ========== FAQ ==========
    add_h(doc, "PHU LUC: 10 CAU HOI THAY/CO CO THE HOI + GOI Y TRA LOI", level=1)

    faqs = [
        ("Vi sao khong dung model to hon nua (yolov8l, yolov8x)?",
         "yolov8s da du chat luong (mAP 0.843). Model to hon train mat 10-24h thay vi 5.5h, khong dang cho bai "
         "tap sinh vien. Neu deploy production thi co the can nhac tuy nhu cau."),
        ("Vi sao chi test tren 5.9 giay video? Co du dai khong?",
         "Do la video demo. Nhom em cung eval tren tap test 56 nghin anh de danh gia detection - do la metric "
         "chuan ML. Counting tren video dai hon can dem tay ground truth - ton nhieu thoi gian, se lam trong "
         "phan mo rong."),
        ("Fine-tune nghia la gi cu the?",
         "Bat dau tu model YOLOv8s da duoc train tren tap COCO (nen model da biet 'xe hoi', 'xe may',... nhung "
         "chua quen goc quay camera giao thong). Ta 'day them' bang du lieu VN qua 50 epoch, moi epoch model "
         "xem het 68 nghin anh 1 lan. Sau 50 lan, model quen voi goc quay + dac diem xe VN."),
        ("Vi sao gom van vao truck? Co the giu 5 class 'motorcycle, car, bus, van, truck' duoc khong?",
         "Co the, nhung se lam schema phuc tap va van co the confusion vi UA-DETRAC gan van la 1 class rieng "
         "trong khi VN CanTho khong co van. Gom vao truck la trade-off don gian hon. Neu co du data van rieng, "
         "co the tach 5 class trong tuong lai."),
        ("ByteTrack la gi? Co gi hay hon SORT/DeepSORT?",
         "ByteTrack (2022) la thuat toan tracking SOTA. Diem manh: khong can re-ID model rieng nhu DeepSORT, "
         "nhanh + nhe hon. Cach hoat dong: gan bounding box cua frame moi voi track cu bang IoU + Kalman filter, "
         "co 2 stage de tan dung ca low-conf detections."),
        ("Duong ke dem tai sao chinh xac? Xe co the qua rat nhanh?",
         "Voi 30 FPS, moi 33ms co 1 frame. Xe co van toc 80 km/h di 33ms = 0.73m - nho hon kich thuoc xe (~4m). "
         "Nen giua 2 frame lien tiep tam xe di chuyen 1 khoang nho, dam bao co segment cat qua line. Neu can "
         "chac chan hon, tang FPS len 60."),
        ("Model chay bao nhieu FPS tren GPU?",
         "Tren RTX 3500 Ada 12GB voi image size 512, FP16: khoang 85 FPS trong che do inference. Video 30 FPS "
         "nen thoa man realtime, con du tai nguyen cho hien thi UI."),
        ("Van con detect duoc xe khi troi mua/dem khong?",
         "Han che. Dataset training chu yeu la anh ban ngay, thoi tiet tot. De hoat dong tot trong dieu kien "
         "khac, can bo sung dataset da dang (dem, mua, suong mu) + augmentation. Do la huong phat trien tiep."),
        ("Neu co 2 xe di sat nhau, co dem duoc dung khong?",
         "Voi tracking ByteTrack, moi xe co ID rieng nen se dem thanh 2. Van de xay ra khi 2 xe che khuat nhau "
         "hoan toan trong nhieu frame - model co the nham. Trong test video demo, ty le nay thap nen counting "
         "van dat 99%."),
        ("Neu deploy that su ngoai duong, cai gi kho nhat?",
         "3 kho khan: (1) chat luong camera - anh mo do gio thu do cao; (2) goc quay khac voi training data; "
         "(3) chieu sang thay doi trong ngay. Cach xu ly: bo sung du lieu quay tu camera thuc te, retrain "
         "model theo tung cai dat cu the."),
    ]
    for q, a in faqs:
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(8)
        r = p.add_run(f"Q: {q}")
        set_font(r, size=11, bold=True)
        p = doc.add_paragraph()
        r = p.add_run(f"A: {a}")
        set_font(r, size=11)

    doc.save(str(OUT))
    print(f"[OK] Da sinh: {OUT}")
    print(f"     Kich thuoc: {OUT.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    main()
