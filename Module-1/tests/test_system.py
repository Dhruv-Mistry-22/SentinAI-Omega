"""
tests/test_system.py — Automated end-to-end test suite.

Run from project root with:
    python tests/test_system.py
"""

import os
import sys
import traceback
import time

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PASS = "  [PASS]"
FAIL = "  [FAIL]"
SEP  = "-" * 62

results = []

def record(name, passed, detail=""):
    status = PASS if passed else FAIL
    results.append((name, passed, detail))
    print(f"{status}  {name}")
    if detail:
        print(f"         -> {detail}")


def section(title):
    print(f"\n{SEP}")
    print(f"  {title}")
    print(SEP)


# ════════════════════════════════════════════════════════════
#  MODULE 1 — cleaner.py
# ════════════════════════════════════════════════════════════
section("MODULE: src/cleaner.py")

try:
    from src.cleaner import clean_for_comparison, ensure_nltk_data

    text = "Roll No: 12345\nThe water cycle is important."
    cleaned = clean_for_comparison(text)
    passed = "12345" not in cleaned and "water cycle" in cleaned
    record("Strips roll number metadata", passed, f"result snippet: '{cleaned[:60]}'")

    text2 = "Date: 12/06/2025\nThis is assignment content."
    cleaned2 = clean_for_comparison(text2)
    record("Strips date metadata", "12/06/2025" not in cleaned2)

    text3 = "HELLO WORLD"
    cleaned3 = clean_for_comparison(text3)
    record("Lowercases text", cleaned3 == "hello world", f"got: '{cleaned3}'")

    try:
        r = clean_for_comparison("")
        record("Handles empty string without crash", True, f"returned: '{r}'")
    except Exception as e:
        record("Handles empty string without crash", False, str(e))

    try:
        ensure_nltk_data()
        record("NLTK data bootstrap (ensure_nltk_data)", True)
    except Exception as e:
        record("NLTK data bootstrap (ensure_nltk_data)", False, str(e))

except Exception as e:
    record("cleaner.py — import / general", False, traceback.format_exc(limit=2))


# ════════════════════════════════════════════════════════════
#  MODULE 2 — reader.py
# ════════════════════════════════════════════════════════════
section("MODULE: src/reader.py")

try:
    from src.reader import scan_folder

    sample_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sample_assignments")

    docs = scan_folder(sample_dir)
    record("scan_folder returns list", isinstance(docs, list), f"{len(docs)} docs found")

    required_keys = {"filename", "content", "metadata"}
    bad = [d for d in docs if not required_keys.issubset(d.keys())]
    record("All docs have required keys", len(bad) == 0)

    txts = [d for d in docs if d["filename"].endswith(".txt")]
    record("Reads .txt files", len(txts) > 0, f"{len(txts)} txt files loaded")

    non_empty = [d for d in docs if d["content"].strip()]
    record("At least 2 docs have non-empty content", len(non_empty) >= 2)

    for d in docs[:1]:
        m = d["metadata"]
        record("Metadata contains file_size", "file_size" in m)
        break

except Exception as e:
    record("reader.py — import / general", False, traceback.format_exc(limit=2))


# ════════════════════════════════════════════════════════════
#  MODULE 3 — ai_detector.py (v3)
# ════════════════════════════════════════════════════════════
section("MODULE: src/ai_detector.py (v4 — 7 metrics)")

try:
    from src.ai_detector import (
        extract_metrics, score_metrics, generate_paragraph_heatmap,
        generate_verdict, evaluate_document, analyze_ai_characteristics,
        METRIC_CONFIG, HUMAN_BASELINES
    )

    HUMAN_TEXT = """
    The water cycle is one of the most fundamental processes on Earth.
    Rain falls from clouds! Rivers rush and tumble — sometimes flooding.
    Plants drink deeply; animals scatter. I've seen it firsthand: muddy boots,
    soaked coats, but the fields turn brilliant green.
    Small streams feed big rivers that carve canyons over time.
    My grandfather called rain "the earth's breath." That stuck with me.
    Different regions experience wildly different rainfall — deserts get almost
    none, while rainforests are drenched. It's chaotic and beautiful.
    Scientists study precipitation patterns to predict droughts and floods.
    Without the water cycle, life on land would simply not exist.
    """ * 3

    AI_TEXT = """
    Furthermore, it is important to note that the water cycle is a crucial process.
    In conclusion, the water cycle plays a significant role in maintaining ecological balance.
    Moreover, it is evident that precipitation is an essential component of the hydrological cycle.
    Additionally, needless to say, evaporation contributes significantly to atmospheric moisture.
    To summarize, having said that, the water cycle is a testament to nature's complexity.
    Building upon this understanding, firstly, we must consider the role of condensation.
    Secondly, it is worth noting that transpiration is also a key factor to consider.
    Ultimately, as previously mentioned, the water cycle sustains all life on Earth.
    """ * 3

    # 13 metrics
    raw_h, _, _, _ = extract_metrics(HUMAN_TEXT)
    record("extract_metrics returns 7 metric keys",
           len(HUMAN_BASELINES) == len(raw_h),
           f"expected 7, got {len(raw_h)}: {list(raw_h.keys())}")

    score_h, _, _ = score_metrics(raw_h)
    raw_a, _, _, _ = extract_metrics(AI_TEXT)
    score_a, _, _ = score_metrics(raw_a)
    record("score_metrics returns int 0-100", isinstance(score_h, int) and 0 <= score_h <= 100, f"score={score_h}")
    record("AI text scores higher than human text", score_a > score_h, f"human={score_h}, ai={score_a}")

    record("METRIC_CONFIG has 7 entries", len(METRIC_CONFIG) == 7, f"got {len(METRIC_CONFIG)}")
    weight_sum = sum(w for _, _, w, _ in METRIC_CONFIG)
    record("METRIC_CONFIG weights sum to 1.0", abs(weight_sum - 1.0) < 0.001, f"sum={weight_sum:.6f}")

    res = evaluate_document(HUMAN_TEXT)
    required = {
        "writing_characteristics_score", "assessment", "confidence",
        "indicators", "section_analysis", "component_scores",
        "verdict", "verdict_summary", "ai_paragraph_pct",
        "mixed_paragraph_pct", "paragraph_heatmap"
    }
    missing = required - set(res.keys())
    record("evaluate_document returns all required keys", len(missing) == 0,
           f"missing: {missing}" if missing else "")

    batch = {"doc1.txt": HUMAN_TEXT, "doc2.txt": AI_TEXT}
    batch_result = analyze_ai_characteristics(batch)
    record("analyze_ai_characteristics processes batch",
           set(batch_result.keys()) == {"doc1.txt", "doc2.txt"})

    record("New metric 'hedge_density' in component_scores",
           "hedge_density" in res.get("component_scores", {}),
           str(list(res.get("component_scores", {}).keys())))
    # passive_ratio and starter_variety were tested and rejected in v4 (see ai_detector.py docstring)
    record("Rejected metric 'passive_ratio' NOT in component_scores (v4 correct)",
           "passive_ratio" not in res.get("component_scores", {}))
    record("Rejected metric 'starter_variety' NOT in component_scores (v4 correct)",
           "starter_variety" not in res.get("component_scores", {}))

except Exception as e:
    record("ai_detector.py — import / general", False, traceback.format_exc(limit=3))


# ════════════════════════════════════════════════════════════
#  MODULE 4 — style_analyzer.py
# ════════════════════════════════════════════════════════════
section("MODULE: src/style_analyzer.py")

try:
    from src.style_analyzer import compute_style_vector, compare_styles

    text_a = "The dog ran fast. It barked loudly! Then it stopped."
    text_b = "A cat sat quietly. She purred softly. She slept."
    vec_a = compute_style_vector(text_a)
    vec_b = compute_style_vector(text_b)
    record("compute_style_vector returns a value", vec_a is not None)
    sim = compare_styles(vec_a, vec_b)
    record("compare_styles returns float in [0, 1]",
           isinstance(sim, float) and 0.0 <= sim <= 1.0, f"sim={sim:.4f}")
    sim_same = compare_styles(vec_a, vec_a)
    record("compare_styles identical texts -> ~1.0", sim_same > 0.95, f"got {sim_same:.4f}")

except Exception as e:
    record("style_analyzer.py — import / general", False, traceback.format_exc(limit=2))


# ════════════════════════════════════════════════════════════
#  MODULE 5 — analyzer.py
# ════════════════════════════════════════════════════════════
section("MODULE: src/analyzer.py (SimilarityAnalyzer)")

try:
    from src.analyzer import SimilarityAnalyzer
    import numpy as np

    files = ["a.txt", "b.txt", "c.txt"]
    shared = ("The mitochondria is the powerhouse of the cell. "
              "It produces ATP through cellular respiration. ") * 5
    texts = {
        "a.txt": shared,
        "b.txt": shared + " Additional sentence from student B.",
        "c.txt": ("The French Revolution began in 1789. "
                  "Citizens stormed the Bastille. ") * 5,
    }

    analyzer = SimilarityAnalyzer()
    result = analyzer.analyze(files, texts, texts)

    required = {"files", "tfidf_matrix", "jaccard_matrix",
                "structural_matrix", "style_matrix", "combined_matrix"}
    missing = required - set(result.keys())
    record("SimilarityAnalyzer.analyze returns all matrix keys", len(missing) == 0)

    n = len(files)
    for key in ["tfidf_matrix", "jaccard_matrix", "combined_matrix"]:
        m = result[key]
        record(f"{key} is {n}x{n} matrix", m.shape == (n, n))

    ab = result["combined_matrix"][0][1]
    ac = result["combined_matrix"][0][2]
    record("Similar docs score higher than unrelated docs",
           ab > ac, f"a<->b={ab:.3f}, a<->c={ac:.3f}")

    diag = [result["tfidf_matrix"][i][i] for i in range(n)]
    record("TF-IDF diagonal is zeroed out", all(v == 0.0 for v in diag))

except Exception as e:
    record("analyzer.py — import / general", False, traceback.format_exc(limit=3))


# ════════════════════════════════════════════════════════════
#  MODULE 6 — classifier.py
# ════════════════════════════════════════════════════════════
section("MODULE: src/classifier.py")

try:
    from src.classifier import classify_score, determine_original

    record("classify_score >= 0.85 -> COPIED",   classify_score(0.90) == "COPIED")
    record("classify_score 0.60 -> SUSPICIOUS",  classify_score(0.60) == "SUSPICIOUS")
    record("classify_score 0.30 -> ORIGINAL",    classify_score(0.30) == "ORIGINAL")

    import time as _time
    now = _time.time()
    doc_old = {"filename": "old.txt", "metadata": {"modified_time": now - 7200, "created_time": now - 10000, "file_size": 1000}}
    doc_new = {"filename": "new.txt", "metadata": {"modified_time": now,         "created_time": now - 5000,  "file_size": 1000}}
    auth = determine_original(doc_old, doc_new)
    record("determine_original picks earlier-modified as original",
           auth["original"] == "old.txt", f"original={auth['original']}")

except Exception as e:
    record("classifier.py — import / general", False, traceback.format_exc(limit=2))


# ════════════════════════════════════════════════════════════
#  MODULE 7 — sentence_matcher.py
# ════════════════════════════════════════════════════════════
section("MODULE: src/sentence_matcher.py")

try:
    from src.sentence_matcher import find_matching_sentences

    text1 = "Shared content appears in both documents. The quick fox jumps. Unique line one."
    text2 = "The quick fox jumps. Shared content appears in both documents. Unique line two."
    matches = find_matching_sentences(text1, text2)
    record("find_matching_sentences returns a list", isinstance(matches, list))
    record("Detects known shared sentences", len(matches) > 0, f"{len(matches)} match(es)")

    try:
        r = find_matching_sentences("", "")
        record("Handles empty strings without crash", True)
    except Exception as e:
        record("Handles empty strings without crash", False, str(e))

except Exception as e:
    record("sentence_matcher.py — import / general", False, traceback.format_exc(limit=2))


# ════════════════════════════════════════════════════════════
#  MODULE 8 — utils.py
# ════════════════════════════════════════════════════════════
section("MODULE: src/utils.py")

try:
    from src.utils import progress_bar, format_time

    record("format_time returns string", isinstance(format_time(1.5), str))
    record("format_time for 120 seconds", isinstance(format_time(120), str), format_time(120))
    try:
        progress_bar(5, 10, "Test")
        record("progress_bar runs without crash", True)
    except Exception as e:
        record("progress_bar runs without crash", False, str(e))

except Exception as e:
    record("utils.py — import / general", False, traceback.format_exc(limit=2))


# ════════════════════════════════════════════════════════════
#  INTEGRATION TEST — Full pipeline
# ════════════════════════════════════════════════════════════
section("INTEGRATION: Full Pipeline")

try:
    from src.reader import scan_folder
    from src.cleaner import clean_for_comparison, ensure_nltk_data
    from src.analyzer import SimilarityAnalyzer
    from src.sentence_matcher import find_matching_sentences
    from src.classifier import classify_all_pairs, get_document_verdicts
    from src.ai_detector import analyze_ai_characteristics

    sample_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sample_assignments")

    ensure_nltk_data()
    documents = scan_folder(sample_dir)
    documents = [d for d in documents if len(d["content"].split()) >= 30]
    files = [d["filename"] for d in documents]

    record("Integration: loaded valid documents", len(files) >= 2, f"{len(files)} docs")

    if len(files) >= 2:
        raw_texts     = {d["filename"]: d["content"] for d in documents}
        cleaned_texts = {d["filename"]: clean_for_comparison(d["content"]) for d in documents}

        t0 = time.time()
        analyzer = SimilarityAnalyzer()
        analysis = analyzer.analyze(files, cleaned_texts, raw_texts)
        elapsed = time.time() - t0
        record("Integration: SimilarityAnalyzer completes", True, f"{elapsed:.2f}s")

        flagged = classify_all_pairs(analysis, documents)
        verdicts = get_document_verdicts(files, flagged)
        record("Integration: classify_all_pairs completes", isinstance(flagged, list), f"{len(flagged)} flagged")
        record("Integration: verdicts for all docs", len(verdicts) == len(files))

        a_b_flagged = any(
            ("student_A.txt" in p["file1"] or "student_A.txt" in p["file2"]) and
            ("student_B.txt" in p["file1"] or "student_B.txt" in p["file2"])
            for p in flagged
        )
        record("Integration: student_A <-> student_B detected",
               a_b_flagged, f"{len(flagged)} total flagged pairs")

        t0 = time.time()
        ai_res = analyze_ai_characteristics(raw_texts)
        elapsed = time.time() - t0
        record("Integration: AI analysis completes (v3)", len(ai_res) == len(files),
               f"{elapsed:.2f}s, 13-metric v3")

        for fname, res in list(ai_res.items())[:1]:
            req = {"writing_characteristics_score", "assessment", "confidence",
                   "indicators", "section_analysis", "component_scores", "verdict"}
            missing = req - set(res.keys())
            record("Integration: AI result schema correct", len(missing) == 0,
                   f"score={res['writing_characteristics_score']}, verdict={res['verdict']}")
            record("Integration: v3/v4 hedge_density metric present in component_scores",
                   "hedge_density" in res["component_scores"])

except Exception as e:
    record("Integration pipeline — crashed", False, traceback.format_exc(limit=4))


# ════════════════════════════════════════════════════════════
#  FINAL REPORT
# ════════════════════════════════════════════════════════════
print(f"\n{'=' * 62}")
print("  FINAL TEST REPORT")
print('=' * 62)

passed = [r for r in results if r[1]]
failed = [r for r in results if not r[1]]

print(f"\n  Total tests : {len(results)}")
print(f"  Passed      : {len(passed)}")
print(f"  Failed      : {len(failed)}")
print(f"  Pass rate   : {len(passed)/len(results)*100:.1f}%\n")

if failed:
    print("  --- FAILED TESTS ---")
    for name, _, detail in failed:
        print(f"  x  {name}")
        if detail:
            print(f"       {detail[:120]}")
    print()

if len(failed) == 0:
    print("  ALL TESTS PASSED -- System is functioning correctly.\n")
elif len(failed) <= 3:
    print("  MOSTLY PASSING -- Minor issues detected.\n")
else:
    print("  MULTIPLE FAILURES -- System has significant issues.\n")
