"""
main.py — Entry point for the Assignment Plagiarism Detection System.

CLI workflow:
  1. Read folder of assignments (PDF / DOCX / TXT)
  2. Clean & preprocess every document
  3. Run 4-layer similarity analysis (scalable to 500+ docs)
  4. Classify pairs  ->  COPIED / SUSPICIOUS / ORIGINAL
  5. Collect sentence-level evidence for flagged pairs
  6. Run AI Writing Characteristics Analysis (always enabled)
  7. Generate PDF report + Excel spreadsheet
"""

import os
import sys
import time

from src.reader import scan_folder
from src.cleaner import clean_for_comparison, ensure_nltk_data
from src.analyzer import SimilarityAnalyzer
from src.sentence_matcher import find_matching_sentences
from src.classifier import classify_all_pairs, get_document_verdicts
from src.report_generator import generate_pdf_report
from src.excel_exporter import export_excel
from src.ai_detector import analyze_ai_characteristics
from src.utils import (
    print_header, print_success, print_error,
    print_warning, print_info, format_time, progress_bar,
)


# ────────────────────── MAIN ──────────────────────

def main():
    print_header("ASSIGNMENT PLAGIARISM DETECTION SYSTEM")
    print("  4-layer similarity engine  |  PDF / DOCX / TXT")
    print("  Scalable to 500+ documents |  CLI mode\n")

    # ── 1. Folder path ──────────────────────────────────
    folder = input("  Enter folder path containing assignments: ").strip()
    folder = folder.strip('"').strip("'")      # remove drag-and-drop quotes

    if not os.path.isdir(folder):
        print_error(f"Folder not found: {folder}")
        return

    # ── 2. Bootstrap NLP resources ──────────────────────
    print_info("Initializing NLP engine ...")
    ensure_nltk_data()

    # ── 3. Read documents ───────────────────────────────
    print_header("STEP 1: Reading Documents")
    t0 = time.time()

    documents = scan_folder(folder)

    if len(documents) < 2:
        print_error(f"Need at least 2 valid documents — found {len(documents)}.")
        return

    print_success(f"Loaded {len(documents)} documents in {format_time(time.time() - t0)}")
    for doc in documents:
        kb = doc["metadata"]["file_size"] / 1024
        print(f"    - {doc['filename']}  ({kb:.1f} KB)")

    # ── 4. Clean / preprocess ───────────────────────────
    print_header("STEP 2: Cleaning & Preprocessing")
    t0 = time.time()

    files = [d["filename"] for d in documents]
    raw_texts = {}
    cleaned_texts = {}

    for i, doc in enumerate(documents):
        progress_bar(i + 1, len(documents), "  Cleaning")
        raw_texts[doc["filename"]] = doc["content"]
        cleaned_texts[doc["filename"]] = clean_for_comparison(doc["content"])

    # Drop documents that become empty after cleaning
    empty = [f for f in files if not cleaned_texts[f].strip()]
    if empty:
        print_warning(f"Skipping {len(empty)} empty doc(s): {empty}")
        for f in empty:
            files.remove(f)
            del cleaned_texts[f]
            del raw_texts[f]
            documents = [d for d in documents if d["filename"] != f]

    if len(files) < 2:
        print_error("Not enough valid documents after cleaning.")
        return

    print_success(f"Preprocessing done in {format_time(time.time() - t0)}")

    # ── 5. Multi-layer similarity analysis ──────────────
    print_header("STEP 3: Multi-Layer Similarity Analysis")
    t0 = time.time()

    analyzer = SimilarityAnalyzer()
    analysis = analyzer.analyze(files, cleaned_texts, raw_texts)

    print_success(f"Analysis done in {format_time(time.time() - t0)}")

    # ── 6. Classification & authorship ──────────────────
    print_header("STEP 4: Classification & Authorship Detection")
    t0 = time.time()

    flagged_pairs = classify_all_pairs(analysis, documents)
    verdicts = get_document_verdicts(files, flagged_pairs)

    print_success(f"Classification done in {format_time(time.time() - t0)}")

    # ── 7. Sentence-level evidence  (flagged only) ──────
    sentence_evidence = {}
    if flagged_pairs:
        print_header("STEP 5: Sentence-Level Evidence Collection")
        t0 = time.time()

        for i, pair in enumerate(flagged_pairs):
            progress_bar(i + 1, len(flagged_pairs), "  Matching")
            key = (pair["file1"], pair["file2"])
            sentence_evidence[key] = find_matching_sentences(
                raw_texts[pair["file1"]],
                raw_texts[pair["file2"]],
            )

        print_success(f"Evidence collected in {format_time(time.time() - t0)}")

    # ── 8. Console results ──────────────────────────────
    copied_n = sum(1 for v in verdicts.values() if v["status"] == "COPIED")
    suspicious_n = sum(1 for v in verdicts.values() if v["status"] == "SUSPICIOUS")
    original_n = sum(1 for v in verdicts.values() if v["status"] == "ORIGINAL")

    print_header("RESULTS SUMMARY")
    print(f"\n  Total Documents : {len(files)}")
    print(f"  [COPIED]        : {copied_n}")
    print(f"  [SUSPICIOUS]    : {suspicious_n}")
    print(f"  [ORIGINAL]      : {original_n}")

    if flagged_pairs:
        print(f"\n  Top Flagged Pairs:")
        for p in flagged_pairs[:10]:
            tag = "[COPIED]" if p["classification"] == "COPIED" else "[SUSPICIOUS]"
            print(f"    {tag} {p['file1']} <-> {p['file2']}: "
                  f"{p['combined_score']:.2%}")
            print(f"           Original: {p['original']}  |  "
                  f"Copier: {p['copier']}")

    print("\n  Per-Document Verdicts:")
    for fname in sorted(files):
        v = verdicts[fname]
        tag = f"[{v['status']}]"
        extra = f"  (copied from {v['copied_from']})" if v["copied_from"] else ""
        print(f"    {tag:15s} {fname}{extra}")

    # ── 9. AI Writing Characteristics Analysis (always on) ──
    print_header("STEP 6: AI Writing Characteristics Analysis")
    t0 = time.time()
    ai_results = analyze_ai_characteristics(raw_texts)
    print_success(f"Characteristics Analysis done in {format_time(time.time() - t0)}")

    # Console summary of AI results
    print("\n  AI Writing Characteristics Summary:")
    for fname in sorted(files):
        res = ai_results.get(fname)
        if res:
            score = res["writing_characteristics_score"]
            verdict = res.get("verdict", "N/A")
            print(f"    {fname:<35}  Score: {score:3d}%  Verdict: {verdict}")

    # ── 10. Report generation ────────────────────────────
    print_header("STEP 7: Report Generation")

    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
    os.makedirs(out_dir, exist_ok=True)

    pdf_path  = os.path.join(out_dir, "plagiarism_report.pdf")
    xlsx_path = os.path.join(out_dir, "plagiarism_report.xlsx")

    # PDF
    try:
        generate_pdf_report(
            analysis, flagged_pairs, verdicts,
            sentence_evidence, pdf_path, ai_results
        )
        print_success(f"PDF  report -> {pdf_path}")
    except Exception as exc:
        print_error(f"PDF generation failed: {exc}")
        pdf_path = None

    # Excel
    try:
        export_excel(analysis, flagged_pairs, verdicts, xlsx_path, ai_results)
        print_success(f"Excel report -> {xlsx_path}")
    except Exception as exc:
        print_error(f"Excel generation failed: {exc}")
        xlsx_path = None

    print_header("ANALYSIS COMPLETE")
    print("  Reports saved to the output/ directory.\n")


# ────────────────────────────────────────────────────────

if __name__ == "__main__":
    main()
