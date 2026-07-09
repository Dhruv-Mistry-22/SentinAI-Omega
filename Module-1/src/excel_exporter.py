"""
excel_exporter.py — Excel summary export for teacher records.

Produces a workbook with three sheets:

  1. Summary          – one row per document with verdict
  2. Similarity Matrix – full NxN colour-coded matrix
  3. Flagged Pairs     – detailed view of COPIED / SUSPICIOUS pairs
"""

import os

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter


# ────────────────────── STYLE CONSTANTS ──────────────────────

_THIN = Side(style="thin")
THIN_BORDER = Border(left=_THIN, right=_THIN, top=_THIN, bottom=_THIN)
HEADER_FILL = PatternFill("solid", fgColor="323246")
HEADER_FONT = Font(color="FFFFFF", bold=True, size=10)

RED_FILL = PatternFill("solid", fgColor="FFE0E0")
YELLOW_FILL = PatternFill("solid", fgColor="FFF9DC")
GREEN_FILL = PatternFill("solid", fgColor="E6FFE6")
LIGHT_YELLOW = PatternFill("solid", fgColor="FFFDE7")


def _status_fill(status):
    return {"COPIED": RED_FILL, "SUSPICIOUS": YELLOW_FILL}.get(status, GREEN_FILL)


def _score_fill(score):
    if score >= 0.85:
        return RED_FILL
    if score >= 0.50:
        return YELLOW_FILL
    if score >= 0.25:
        return LIGHT_YELLOW
    return GREEN_FILL


def _auto_width(ws, col, extra=4, cap=50):
    """Set column width based on longest cell value."""
    mx = 0
    for row in ws.iter_rows(min_col=col, max_col=col):
        for cell in row:
            mx = max(mx, len(str(cell.value or "")))
    ws.column_dimensions[get_column_letter(col)].width = min(mx + extra, cap)


# ────────────────────── PUBLIC API ──────────────────────

def export_excel(analysis_result, flagged_pairs, verdicts, output_path, ai_results=None):
    """
    Write analysis results to *output_path* as an ``.xlsx`` workbook.
    """
    wb = Workbook()
    files = analysis_result["files"]
    combined = analysis_result["combined_matrix"]

    # ═══════════════════ Sheet 1: Summary ═══════════════════
    ws1 = wb.active
    ws1.title = "Summary"

    headers = ["#", "Document", "Status", "Copied From",
                "Max Score", "Details"]
    for c, h in enumerate(headers, 1):
        cell = ws1.cell(row=1, column=c, value=h)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL
        cell.alignment = Alignment(horizontal="center")
        cell.border = THIN_BORDER

    for idx, fname in enumerate(sorted(files), 1):
        v = verdicts[fname]
        r = idx + 1

        ws1.cell(r, 1, idx).border = THIN_BORDER

        ws1.cell(r, 2, fname).border = THIN_BORDER

        sc = ws1.cell(r, 3, v["status"])
        sc.fill = _status_fill(v["status"])
        sc.alignment = Alignment(horizontal="center")
        sc.border = THIN_BORDER

        ws1.cell(r, 4, v["copied_from"] or "-").border = THIN_BORDER

        mc = ws1.cell(r, 5, round(v["max_score"], 4) if v["max_score"] else 0)
        mc.number_format = "0.00%"
        mc.border = THIN_BORDER

        detail_text = "; ".join(v["details"][:3])
        ws1.cell(r, 6, detail_text).border = THIN_BORDER

    for c in range(1, len(headers) + 1):
        _auto_width(ws1, c)

    # ═══════════════════ Sheet 2: Similarity Matrix ═══════════════════
    ws2 = wb.create_sheet("Similarity Matrix")

    # top-left corner
    corner = ws2.cell(1, 1, "Document")
    corner.font = HEADER_FONT
    corner.fill = HEADER_FILL
    corner.border = THIN_BORDER

    # column headers
    for j, fname in enumerate(files, 2):
        c = ws2.cell(1, j, fname[:20])
        c.font = HEADER_FONT
        c.fill = HEADER_FILL
        c.alignment = Alignment(horizontal="center", text_rotation=45)
        c.border = THIN_BORDER

    # data
    for i, fname in enumerate(files):
        r = i + 2
        ws2.cell(r, 1, fname).border = THIN_BORDER

        for j in range(len(files)):
            col = j + 2
            score = combined[i][j] if i != j else 1.0
            c = ws2.cell(r, col, round(float(score), 4))
            c.number_format = "0.00%"
            c.alignment = Alignment(horizontal="center")
            c.border = THIN_BORDER
            if i != j:
                c.fill = _score_fill(score)

    # ═══════════════════ Sheet 3: Flagged Pairs ═══════════════════
    ws3 = wb.create_sheet("Flagged Pairs")

    ph = ["#", "Document 1", "Document 2", "Combined", "TF-IDF",
          "Jaccard", "Structural", "Style", "Status",
          "Original", "Copier", "Reason"]
    for c, h in enumerate(ph, 1):
        cell = ws3.cell(1, c, h)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL
        cell.alignment = Alignment(horizontal="center")
        cell.border = THIN_BORDER

    score_keys = ["combined_score", "tfidf_score", "jaccard_score",
                  "structural_score", "style_score"]

    for idx, pair in enumerate(flagged_pairs, 1):
        r = idx + 1

        ws3.cell(r, 1, idx).border = THIN_BORDER
        ws3.cell(r, 2, pair["file1"]).border = THIN_BORDER
        ws3.cell(r, 3, pair["file2"]).border = THIN_BORDER

        for ci, key in enumerate(score_keys, 4):
            c = ws3.cell(r, ci, round(pair[key], 4))
            c.number_format = "0.00%"
            c.fill = _score_fill(pair[key])
            c.border = THIN_BORDER

        sc = ws3.cell(r, 9, pair["classification"])
        sc.fill = _status_fill(pair["classification"])
        sc.alignment = Alignment(horizontal="center")
        sc.border = THIN_BORDER

        ws3.cell(r, 10, pair["original"]).border = THIN_BORDER
        ws3.cell(r, 11, pair["copier"]).border = THIN_BORDER
        ws3.cell(r, 12, pair["reason"]).border = THIN_BORDER

    for c in range(1, len(ph) + 1):
        _auto_width(ws3, c)

    # ═══════════════════ Sheet 4: Characteristics Analysis ═══════════════════
    if ai_results:
        ws4 = wb.create_sheet("Characteristics Analysis")

        ah = [
            "#", "Document", "Characteristics Score", "Assessment", "Confidence",
            "Intro Section", "Body Section", "Conclusion Section",
            "Sentence Uniformity", "Burstiness", "Vocabulary", "Transition Phrase", 
            "Structural", "Repetition", "Paragraph", "Predictability", 
            "Entropy", "Style Consistency", "Indicators"
        ]
        for c, h in enumerate(ah, 1):
            cell = ws4.cell(1, c, h)
            cell.font = HEADER_FONT
            cell.fill = HEADER_FILL
            cell.alignment = Alignment(horizontal="center")
            cell.border = THIN_BORDER

        for idx, fname in enumerate(sorted(files), 1):
            res = ai_results.get(fname)
            if not res:
                continue

            r = idx + 1
            ws4.cell(r, 1, idx).border = THIN_BORDER
            ws4.cell(r, 2, fname).border = THIN_BORDER
            
            sc_c = ws4.cell(r, 3, res["writing_characteristics_score"])
            sc_c.alignment = Alignment(horizontal="center")
            sc_c.border = THIN_BORDER
            
            if res["writing_characteristics_score"] > 75:
                fill_color = RED_FILL
            elif res["writing_characteristics_score"] > 50:
                fill_color = YELLOW_FILL
            else:
                fill_color = GREEN_FILL
                
            sc_c.fill = fill_color

            cl_c = ws4.cell(r, 4, res["assessment"])
            cl_c.fill = fill_color
            cl_c.alignment = Alignment(horizontal="center")
            cl_c.border = THIN_BORDER

            ws4.cell(r, 5, res["confidence"]).border = THIN_BORDER
            
            # Sections
            secs = res.get("section_analysis", {})
            ws4.cell(r, 6, secs.get("Introduction", "")).border = THIN_BORDER
            ws4.cell(r, 7, secs.get("Body", "")).border = THIN_BORDER
            ws4.cell(r, 8, secs.get("Conclusion", "")).border = THIN_BORDER
            
            # Component scores
            comps = res.get("component_scores", {})
            keys = [
                "sentence_uniformity", "burstiness", "vocabulary_distribution", 
                "transition_phrase", "structural_consistency", "repetition_pattern", 
                "paragraph_uniformity", "statistical_predictability", 
                "entropy", "writing_style_consistency"
            ]
            for ci, key in enumerate(keys, 9):
                c_val = ws4.cell(r, ci, round(comps.get(key, 0.0), 4))
                c_val.number_format = "0.00"
                c_val.alignment = Alignment(horizontal="center")
                c_val.border = THIN_BORDER

            ws4.cell(r, 19, "; ".join(res["indicators"])).border = THIN_BORDER

        for c in range(1, len(ah) + 1):
            _auto_width(ws4, c)

    # ── Save ──
    out_dir = os.path.dirname(output_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    wb.save(output_path)
