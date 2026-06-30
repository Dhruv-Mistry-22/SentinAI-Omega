"""
report_generator.py — Professional PDF report generation.

Produces a colour-coded, multi-section PDF report using ``fpdf2``:

  1. Title page with statistics
  2. Executive summary
  3. Per-document verdicts table
  4. Similarity matrix (colour-coded)
  5. Detailed flagged-pair analysis with sentence evidence
  6. Recommendations
  7. AI Writing Characteristics (always included)
"""

import os
from datetime import datetime

import numpy as np
from fpdf import FPDF

from src.utils import make_pdf_safe


# ────────────────────── CUSTOM PDF CLASS ──────────────────────

class ReportPDF(FPDF):
    """Subclass of FPDF with custom header / footer / helpers."""

    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=20)

    # ── Page header ──

    def header(self):
        if self.page_no() == 1:      # skip on title page
            return
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(120, 120, 120)
        self.cell(95, 7, "Assignment Plagiarism Detection Report", align="L")
        self.cell(
            95, 7, datetime.now().strftime("%Y-%m-%d %H:%M"),
            align="R", new_x="LMARGIN", new_y="NEXT",
        )
        self.set_draw_color(200, 200, 200)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)

    # ── Page footer ──

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(140, 140, 140)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")

    # ── Reusable helpers ──

    def section_title(self, title):
        self.ln(5)
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(30, 30, 30)
        self.cell(0, 10, make_pdf_safe(title), new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(50, 120, 200)
        self.set_line_width(0.5)
        self.line(10, self.get_y(), 80, self.get_y())
        self.set_line_width(0.2)
        self.ln(4)

    def sub_title(self, title):
        self.ln(2)
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(50, 50, 50)
        self.cell(0, 8, make_pdf_safe(title), new_x="LMARGIN", new_y="NEXT")

    def body_text(self, text):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(60, 60, 60)
        self.set_x(self.l_margin)
        self.multi_cell(0, 5, make_pdf_safe(text))

    def bullet(self, text):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(60, 60, 60)
        indent = 8
        self.set_x(self.l_margin + indent)
        self.multi_cell(self.epw - indent, 5, make_pdf_safe(f"- {text}"))

    def status_badge(self, status):
        colours = {
            "COPIED":     (220, 53, 69, 255, 255, 255),
            "SUSPICIOUS": (255, 193, 7, 0, 0, 0),
            "ORIGINAL":   (40, 167, 69, 255, 255, 255),
        }
        bg_r, bg_g, bg_b, fg_r, fg_g, fg_b = colours.get(
            status, (128, 128, 128, 255, 255, 255)
        )
        self.set_fill_color(bg_r, bg_g, bg_b)
        self.set_text_color(fg_r, fg_g, fg_b)
        self.set_font("Helvetica", "B", 9)
        w = self.get_string_width(status) + 10
        self.cell(w, 6, f" {status} ", fill=True)
        self.set_text_color(0, 0, 0)


# ────────────────────── REPORT BUILDER ──────────────────────

def generate_pdf_report(
    analysis_result, flagged_pairs, verdicts,
    sentence_evidence, output_path, ai_results=None
):
    """
    Build and save the full PDF report.

    Parameters
    ----------
    analysis_result : dict from ``SimilarityAnalyzer.analyze``
    flagged_pairs   : list from ``classify_all_pairs``
    verdicts        : dict from ``get_document_verdicts``
    sentence_evidence : dict  {(file1, file2): [match_dicts]}
    output_path     : str   destination file path
    ai_results      : dict  from ``analyze_ai_characteristics`` (always provided)
    """
    pdf = ReportPDF()
    pdf.alias_nb_pages()

    files = analysis_result["files"]
    combined = analysis_result["combined_matrix"]

    copied_n = sum(1 for v in verdicts.values() if v["status"] == "COPIED")
    suspicious_n = sum(1 for v in verdicts.values() if v["status"] == "SUSPICIOUS")
    original_n = sum(1 for v in verdicts.values() if v["status"] == "ORIGINAL")

    # ═══════════════════ 1. TITLE PAGE ═══════════════════
    pdf.add_page()
    pdf.ln(30)
    pdf.set_font("Helvetica", "B", 24)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 14, "ASSIGNMENT PLAGIARISM", align="C",
             new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 14, "DETECTION REPORT", align="C",
             new_x="LMARGIN", new_y="NEXT")

    pdf.ln(10)
    pdf.set_font("Helvetica", "", 12)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 8,
             f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}",
             align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 8, f"Total Documents Analyzed: {len(files)}",
             align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(8)
    for label, count, colour in [
        ("COPIED", copied_n, (220, 53, 69)),
        ("SUSPICIOUS", suspicious_n, (255, 165, 0)),
        ("ORIGINAL", original_n, (40, 167, 69)),
    ]:
        pdf.set_font("Helvetica", "B", 16)
        pdf.set_text_color(*colour)
        pdf.cell(0, 10, f"{label}: {count}", align="C",
                 new_x="LMARGIN", new_y="NEXT")

    # ═══════════════════ 2. EXECUTIVE SUMMARY ═══════════════════
    pdf.add_page()
    pdf.section_title("1. Executive Summary")

    pdf.body_text(
        f"This report presents the results of an automated plagiarism "
        f"analysis performed on {len(files)} document submissions. "
        f"The system uses a 4-layer similarity engine combining "
        f"TF-IDF Cosine Similarity, N-gram Jaccard Similarity, "
        f"Structural Fingerprinting, and Writing Style Analysis."
    )
    pdf.ln(3)

    pdf.sub_title("Analysis Configuration")
    pdf.bullet(f"Documents analyzed: {len(files)}")
    pdf.bullet(f"Total pairs compared: {len(files) * (len(files) - 1) // 2:,}")
    pdf.bullet("Weights: TF-IDF 40% + Jaccard 30% + Structural 15% + Style 15%")
    pdf.bullet("Thresholds: COPIED >=85% | SUSPICIOUS 50-84% | ORIGINAL <50%")
    pdf.bullet("Supported formats: TXT, PDF, DOCX")

    pdf.ln(3)
    pdf.sub_title("Key Findings")
    pdf.bullet(f"COPIED documents: {copied_n}")
    pdf.bullet(f"SUSPICIOUS documents: {suspicious_n}")
    pdf.bullet(f"ORIGINAL documents: {original_n}")
    pdf.bullet(f"Flagged pairs: {len(flagged_pairs)}")

    if len(files) > 1:
        mask = np.ones_like(combined, dtype=bool)
        np.fill_diagonal(mask, False)
        pdf.bullet(f"Average pairwise similarity: {combined[mask].mean():.2%}")

    # ═══════════════════ 3. PER-DOCUMENT VERDICTS ═══════════════════
    pdf.add_page()
    pdf.section_title("2. Per-Document Verdicts")
    pdf.body_text("Final classification for each submitted document:")
    pdf.ln(3)

    col_w = [10, 60, 28, 50, 30]
    hdrs = ["#", "Document", "Status", "Copied From", "Max Score"]

    # header row
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(50, 50, 70)
    pdf.set_text_color(255, 255, 255)
    for hdr, w in zip(hdrs, col_w):
        pdf.cell(w, 7, hdr, border=1, fill=True, align="C")
    pdf.ln()

    # data rows
    pdf.set_font("Helvetica", "", 9)
    for idx, fname in enumerate(sorted(files), 1):
        v = verdicts[fname]

        if v["status"] == "COPIED":
            pdf.set_fill_color(255, 230, 230)
        elif v["status"] == "SUSPICIOUS":
            pdf.set_fill_color(255, 249, 220)
        else:
            pdf.set_fill_color(230, 255, 230)

        pdf.set_text_color(30, 30, 30)
        safe_name = make_pdf_safe(fname[:28])
        copied_from = make_pdf_safe(str(v["copied_from"] or "-")[:24])
        score_s = f"{v['max_score']:.0%}" if v["max_score"] > 0 else "-"

        pdf.cell(col_w[0], 6, str(idx), border=1, fill=True, align="C")
        pdf.cell(col_w[1], 6, safe_name, border=1, fill=True)
        pdf.cell(col_w[2], 6, v["status"], border=1, fill=True, align="C")
        pdf.cell(col_w[3], 6, copied_from, border=1, fill=True)
        pdf.cell(col_w[4], 6, score_s, border=1, fill=True, align="C")
        pdf.ln()

    # ═══════════════════ 4. SIMILARITY MATRIX ═══════════════════
    if len(files) <= 25:
        pdf.add_page("L")      # landscape
        pdf.section_title("3. Similarity Matrix")
        pdf.body_text(
            "Colour-coded pairwise similarity scores "
            "(combined 4-layer score):"
        )
        pdf.ln(3)

        n_files = len(files)
        lbl_w = 40
        avail = 260 - lbl_w
        cell_sz = max(8, min(18, avail / max(n_files, 1)))
        font_sz = 6 if n_files <= 15 else 5

        # column labels
        pdf.set_font("Helvetica", "B", font_sz)
        pdf.cell(lbl_w, cell_sz, "", border=0)
        for f in files:
            trunc = f[:int(cell_sz / 2)] if len(f) > int(cell_sz / 2) else f
            pdf.cell(cell_sz, cell_sz, make_pdf_safe(trunc),
                     border=1, align="C")
        pdf.ln()

        # rows
        for i, f1 in enumerate(files):
            pdf.set_font("Helvetica", "", font_sz)
            pdf.cell(lbl_w, cell_sz, make_pdf_safe(f1[:20]), border=0)
            for j in range(len(files)):
                sc = combined[i][j] if i != j else 1.0
                if i == j:
                    pdf.set_fill_color(210, 210, 210)
                elif sc >= 0.85:
                    pdf.set_fill_color(220, 53, 69)
                    pdf.set_text_color(255, 255, 255)
                elif sc >= 0.50:
                    pdf.set_fill_color(255, 193, 7)
                    pdf.set_text_color(0, 0, 0)
                elif sc >= 0.25:
                    pdf.set_fill_color(255, 243, 205)
                    pdf.set_text_color(0, 0, 0)
                else:
                    pdf.set_fill_color(230, 255, 230)
                    pdf.set_text_color(0, 0, 0)

                lbl = "-" if i == j else f"{sc:.0%}"
                pdf.cell(cell_sz, cell_sz, lbl, border=1,
                         fill=True, align="C")
                pdf.set_text_color(0, 0, 0)
            pdf.ln()

    # ═══════════════════ 5. FLAGGED PAIRS ═══════════════════
    if flagged_pairs:
        pdf.add_page("P")
        pdf.section_title("4. Flagged Pairs - Detailed Analysis")

        for pidx, pair in enumerate(flagged_pairs, 1):
            # guard against page overflow
            if pdf.get_y() > 230:
                pdf.add_page()

            pdf.sub_title(
                f"Pair {pidx}: "
                f"{make_pdf_safe(pair['file1'])} <-> "
                f"{make_pdf_safe(pair['file2'])}"
            )

            pdf.status_badge(pair["classification"])
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(60, 60, 60)
            pdf.cell(
                0, 6,
                f"  Combined Score: {pair['combined_score']:.2%}",
                new_x="LMARGIN", new_y="NEXT",
            )

            # layer breakdown
            pdf.ln(1)
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(80, 80, 80)
            pdf.bullet(f"TF-IDF Cosine:  {pair['tfidf_score']:.2%}")
            pdf.bullet(f"N-gram Jaccard: {pair['jaccard_score']:.2%}")
            pdf.bullet(f"Structural:     {pair['structural_score']:.2%}")
            pdf.bullet(f"Writing Style:  {pair['style_score']:.2%}")

            # authorship
            pdf.ln(2)
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(180, 0, 0)
            pdf.body_text(f"Likely original: {make_pdf_safe(pair['original'])}")
            pdf.body_text(f"Likely copier:   {make_pdf_safe(pair['copier'])}")
            pdf.set_font("Helvetica", "I", 9)
            pdf.set_text_color(100, 100, 100)
            pdf.body_text(f"Reason: {make_pdf_safe(pair['reason'])}")

            # sentence evidence
            key = (pair["file1"], pair["file2"])
            evidence = sentence_evidence.get(key, [])
            if evidence:
                pdf.ln(2)
                pdf.set_font("Helvetica", "B", 9)
                pdf.set_text_color(50, 50, 50)
                pdf.cell(
                    0, 6,
                    f"Matched Sentences ({len(evidence)} found):",
                    new_x="LMARGIN", new_y="NEXT",
                )
                pdf.set_font("Helvetica", "", 7)
                indent = 6
                for m in evidence[:8]:
                    if pdf.get_y() > 265:
                        pdf.add_page()
                    pdf.set_text_color(180, 0, 0)
                    preview = make_pdf_safe(m["sent1"][:120])
                    pdf.set_x(pdf.l_margin + indent)
                    pdf.multi_cell(
                        pdf.epw - indent, 4,
                        f'[{m["similarity"]:.0%}] "{preview}"',
                    )
                if len(evidence) > 8:
                    pdf.set_text_color(100, 100, 100)
                    pdf.set_x(pdf.l_margin + indent)
                    pdf.multi_cell(
                        pdf.epw - indent, 5,
                        f"... and {len(evidence) - 8} more matched sentences",
                    )

            pdf.ln(5)

    # ═══════════════════ 6. RECOMMENDATIONS ═══════════════════
    pdf.add_page()
    pdf.section_title("5. Recommendations")

    if copied_n > 0:
        pdf.sub_title("Immediate Actions Required")
        pdf.bullet(
            f"{copied_n} document(s) flagged as COPIED - "
            "require immediate review"
        )
        pdf.bullet("Verify flagged pairs manually before disciplinary action")
        pdf.bullet(
            "Check if documents share the same source material legitimately"
        )

    if suspicious_n > 0:
        pdf.sub_title("Further Investigation Needed")
        pdf.bullet(
            f"{suspicious_n} document(s) flagged as SUSPICIOUS - "
            "need manual review"
        )
        pdf.bullet("May indicate partial copying or shared references")

    if original_n == len(files):
        pdf.sub_title("No Issues Detected")
        pdf.body_text(
            "All submissions appear to be original work. "
            "No further action needed."
        )

    pdf.ln(5)
    pdf.sub_title("Methodology Notes")
    pdf.body_text(
        "This analysis uses a 4-layer similarity engine. While highly "
        "accurate, no automated system is perfect. False positives may "
        "occur when documents legitimately share common topic-specific "
        "terminology. Always verify results with manual review before "
        "taking action."
    )

    # ═══════════════════ 7. AI WRITING CHARACTERISTICS ═══════════════════
    if ai_results:
        pdf.add_page()
        pdf.section_title("6. AI Writing Characteristics Analysis")

        pdf.set_text_color(180, 0, 0)
        pdf.set_font("Helvetica", "B", 10)
        pdf.multi_cell(0, 5, make_pdf_safe(
            "IMPORTANT NOTE: This analysis estimates similarity to common AI-generated "
            "writing patterns. It does NOT prove that AI tools were used."
        ))
        pdf.ln(5)

        for fname in sorted(files):
            res = ai_results.get(fname)
            if not res:
                continue

            if pdf.get_y() > 240:
                pdf.add_page()

            pdf.set_font("Helvetica", "B", 11)
            pdf.set_text_color(50, 50, 50)
            pdf.cell(0, 8, make_pdf_safe(fname), new_x="LMARGIN", new_y="NEXT")

            score = res["writing_characteristics_score"]
            verdict = res.get("verdict", "")

            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(60, 60, 60)
            pdf.set_x(pdf.l_margin + 5)
            pdf.cell(50, 6, make_pdf_safe(f"Characteristics Score: {score}%"))

            # Highlight by score
            if score > 75:
                pdf.set_text_color(220, 53, 69)
            elif score > 50:
                pdf.set_text_color(255, 140, 0)
            else:
                pdf.set_text_color(40, 167, 69)

            pdf.cell(100, 6, make_pdf_safe(f"Assessment: {res['assessment']}"))
            pdf.set_text_color(60, 60, 60)
            pdf.cell(40, 6, make_pdf_safe(f"Confidence: {res['confidence']}"), new_x="LMARGIN", new_y="NEXT")

            # Verdict + paragraph stats
            if verdict:
                pdf.set_x(pdf.l_margin + 5)
                pdf.set_font("Helvetica", "B", 9)
                pdf.set_text_color(80, 80, 80)
                ai_pct = res.get("ai_paragraph_pct", 0)
                mixed_pct = res.get("mixed_paragraph_pct", 0)
                pdf.cell(0, 5,
                    make_pdf_safe(f"Verdict: {verdict}  |  AI-like paragraphs: {ai_pct:.1f}%  |  Mixed: {mixed_pct:.1f}%"),
                    new_x="LMARGIN", new_y="NEXT")

            # Component scores breakdown
            if "component_scores" in res and res["component_scores"]:
                pdf.set_x(pdf.l_margin + 5)
                pdf.set_font("Helvetica", "I", 7)
                pdf.set_text_color(100, 100, 100)
                comps = []
                for k, v in res["component_scores"].items():
                    comps.append(f"{k.replace('_', ' ').title()}: {v}")
                pdf.multi_cell(pdf.epw - 5, 4, " | ".join(comps))

            # Section Analysis
            if "section_analysis" in res and res["section_analysis"]:
                pdf.set_x(pdf.l_margin + 5)
                pdf.set_font("Helvetica", "B", 8)
                pdf.set_text_color(80, 80, 80)
                pdf.cell(0, 5, "Section Analysis:", new_x="LMARGIN", new_y="NEXT")
                pdf.set_font("Helvetica", "", 8)
                for sec, val in res["section_analysis"].items():
                    pdf.set_x(pdf.l_margin + 10)
                    pdf.multi_cell(pdf.epw - 10, 4, make_pdf_safe(f"- {sec}: {val}"))

            pdf.set_text_color(60, 60, 60)
            pdf.set_x(pdf.l_margin + 5)
            pdf.set_font("Helvetica", "I", 9)
            pdf.cell(0, 6, "Indicators:", new_x="LMARGIN", new_y="NEXT")

            for ind in res["indicators"]:
                indent = 10
                pdf.set_x(pdf.l_margin + indent)
                pdf.set_font("Helvetica", "", 9)
                pdf.multi_cell(pdf.epw - indent, 5, make_pdf_safe(f"- {ind}"))

            pdf.ln(3)

    # ── Save ──
    out_dir = os.path.dirname(output_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    pdf.output(output_path)
