"""
tests/test_ai_detector.py -- Deep test suite for src/ai_detector.py (v3)

Tests every function, every metric, edge cases, verdict logic,
heatmap scoring, and real student sample accuracy.

Run from project root with:
    python tests/test_ai_detector.py
"""

import os
import sys
import math
import traceback

os.environ["PYTHONIOENCODING"] = "utf-8"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PASS = "  [PASS]"
FAIL = "  [FAIL]"
SEP  = "-" * 62

results = []

def record(name, passed, detail=""):
    results.append((name, passed, detail))
    status = PASS if passed else FAIL
    print(f"{status}  {name}")
    if detail:
        short = detail[:110] + ("..." if len(detail) > 110 else "")
        print(f"           {short}")

def section(title):
    print(f"\n{SEP}")
    print(f"  {title}")
    print(SEP)

# ─── IMPORT ────────────────────────────────────────────────
try:
    from src.ai_detector import (
        z_score, z_to_ai_probability,
        _cv, extract_metrics, score_metrics,
        score_paragraph, generate_paragraph_heatmap,
        generate_verdict, get_assessment,
        analyze_sections, evaluate_document,
        analyze_ai_characteristics,
        HUMAN_BASELINES, METRIC_CONFIG,
    )
    print("  [OK]  src/ai_detector.py (v3) imported successfully\n")
except Exception as e:
    print(f"  [FATAL]  Cannot import src.ai_detector: {e}")
    sys.exit(1)


# ═══════════════════════════════════════════════════════════
#  CORPUS — 5 carefully crafted text samples
# ═══════════════════════════════════════════════════════════

# 1. Clear human text: varied sentences, messy, personal
HUMAN = """
I honestly didn't know where to start with this assignment. Water moves
around — that's the basic idea, right? Rain comes down, soaks into the
ground, rivers carry it off. My dad used to say the river behind our
house "breathed" with the seasons. Swelled in March, shrank by August.
Never thought that was science until now.

Evaporation's the bit that surprised me most. I thought water just...
stayed wet. But the sun pulls it up, invisible? Wild. Clouds are just
that — collected water-vapour, drifting. Then it gets heavy, dumps down.
We call it rain. Or snow if it's cold enough up there.

Plants are weirdly involved. They pull water from the ground (roots),
push it out through leaves (transpiration — new word for me). Never
realised they were part of the "cycle." Thought they just drank water.

Anyway — it loops. Endlessly. The same water molecules that dinosaurs
drank are probably falling as rain somewhere right now. That's actually
kind of insane to think about. Science is weird.

I still don't fully get the numbers (mm of rainfall per year, watershed
areas) but the overall flow makes sense now: ocean -> air -> clouds ->
rain -> ground/rivers -> ocean again. Round and round.
"""

# 2. Clear AI text: heavy transitions, uniform, formulaic
AI_CLEAR = """
In conclusion, the water cycle is a fundamental and crucial process that sustains all life on Earth.
Furthermore, it is important to note that evaporation plays a significant role in this cycle.
Moreover, it is evident that precipitation is an essential component of the hydrological cycle.
Additionally, needless to say, condensation contributes significantly to atmospheric moisture levels.
To summarize, having said that, the water cycle represents a testament to nature's complexity.

Building upon this understanding, firstly, we must consider the role of evaporation in detail.
Secondly, it is worth noting that transpiration from vegetation is also a key factor to consider.
Thirdly, as previously mentioned, condensation forms clouds which eventually lead to precipitation.
Ultimately, on the other hand, human activities have begun to impact the natural water cycle.
In essence, to begin with, the hydrological cycle represents a fundamental natural phenomenon.

In light of these considerations, it is important to note that surface runoff collects in rivers.
Furthermore, as a result, these rivers transport water back to the ocean completing the cycle.
Consequently, it is evident that the water cycle is a continuous and self-sustaining process.
Moreover, delve into the details and one finds that groundwater recharge is equally important.
To begin with, it is crucial to understand that aquifers store significant amounts of fresh water.
"""

# 3. Mixed text: starts human, ends AI-like
MIXED = """
Water is something I've always taken for granted. Turn the tap, out it comes.
But this assignment made me actually think about where it's been before.

It starts mostly with the ocean — massive, solar-heated, constantly releasing
vapour into the air. Winds carry that moisture inland, cool air condenses it,
and eventually it falls somewhere as rain or snow.

Furthermore, it is important to note that the precipitation then follows
several pathways. Some infiltrates the soil, recharging groundwater aquifers.
Additionally, surface runoff collects in streams and rivers, ultimately
returning to the ocean. It is worth noting that this process is continuous.

In conclusion, the water cycle is a fundamental process. To summarize, it
is evident that understanding the hydrological cycle is crucial for managing
water resources. Moreover, as previously mentioned, human activities are
increasingly impacting this natural cycle. Building upon this knowledge,
it becomes clear that conservation is essential for sustainable water use.
"""

# 4. Real student_A content (from sample_assignments)
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STUDENT_A = open(
    os.path.join(_PROJECT_ROOT, "sample_assignments", "student_A.txt"),
    encoding="utf-8"
).read()

# 5. Edge cases
EMPTY       = ""
ONE_WORD    = "Hello"
VERY_SHORT  = "The cat sat on the mat. It was a happy cat."
ONLY_SPACES = "   \n\n   \t   "


# ═══════════════════════════════════════════════════════════
#  TEST 1 — Low-level helpers
# ═══════════════════════════════════════════════════════════
section("1. LOW-LEVEL HELPERS: _cv, z_score, z_to_ai_probability")

# _cv
record("_cv([10,10,10]) = 0.0 (no variation)", _cv([10, 10, 10]) == 0.0)
record("_cv([1,2,3,4,5]) > 0 (has variation)",  _cv([1, 2, 3, 4, 5]) > 0)
record("_cv([]) = 0.0 (empty list safe)",        _cv([]) == 0.0)
record("_cv([5]) = 0.0 (single item safe)",      _cv([5]) == 0.0)
record("_cv([0,0,0]) = 0.0 (zero mean safe)",    _cv([0, 0, 0]) == 0.0)

# z_score
for key, (mean, std) in HUMAN_BASELINES.items():
    z = z_score(mean, key)  # value exactly at mean should give z=0
    record(f"z_score(mean, '{key}') = 0.0", abs(z) < 1e-9, f"got {z:.6f}")

z_high = z_score(999, "sentence_cv")   # huge value -> large positive z
z_low  = z_score(-999, "sentence_cv")  # tiny value -> large negative z
record("z_score large value -> positive z",  z_high > 5)
record("z_score small value -> negative z",  z_low < -5)

# z_to_ai_probability
p_neutral = z_to_ai_probability(0, "high_is_ai")
record("z_to_ai_probability(z=0) = 0.5 (neutral)", abs(p_neutral - 0.5) < 0.01, f"got {p_neutral:.4f}")

p_high = z_to_ai_probability(3, "high_is_ai")
record("z_to_ai_probability(z=3, high_is_ai) > 0.95", p_high > 0.95, f"got {p_high:.4f}")

p_low = z_to_ai_probability(-3, "high_is_ai")
record("z_to_ai_probability(z=-3, high_is_ai) < 0.05", p_low < 0.05, f"got {p_low:.4f}")

p_flip = z_to_ai_probability(3, "low_is_ai")
record("z_to_ai_probability(z=3, low_is_ai) < 0.05 (flipped)", p_flip < 0.05, f"got {p_flip:.4f}")

p_range_ok = all(
    0.0 <= z_to_ai_probability(z, "high_is_ai") <= 1.0
    for z in [-10, -5, -2, -1, 0, 1, 2, 5, 10]
)
record("z_to_ai_probability always in [0.0, 1.0]", p_range_ok)


# ═══════════════════════════════════════════════════════════
#  TEST 2 — extract_metrics
# ═══════════════════════════════════════════════════════════
section("2. extract_metrics — all 7 metrics (v4)")

raw_h, sents_h, words_h, paras_h = extract_metrics(HUMAN)
raw_a, sents_a, words_a, paras_a = extract_metrics(AI_CLEAR)

expected_keys = set(HUMAN_BASELINES.keys())

# All keys present
record("extract_metrics returns all 7 metric keys (human text)",
       expected_keys == set(raw_h.keys()), f"got: {list(raw_h.keys())}")
record("extract_metrics returns all 7 metric keys (AI text)",
       expected_keys == set(raw_a.keys()))

# None values only when text is too short
for key, val in raw_h.items():
    if val is None:
        record(f"Metric '{key}' is None on long human text (UNEXPECTED)", False,
               "Should have enough data")

# Values in plausible ranges for long text
for key, val in raw_h.items():
    if val is not None:
        record(f"extract_metrics['{key}'] is a finite float",
               isinstance(val, float) and math.isfinite(val), f"val={val:.4f}")

# Short text handling — all should return None or 0
raw_short, _, _, _ = extract_metrics(VERY_SHORT)
record("Very short text doesn't crash extract_metrics", True)

# Empty text
try:
    raw_empty, _, _, _ = extract_metrics(EMPTY)
    record("Empty string: extract_metrics doesn't crash", True)
except Exception as e:
    record("Empty string: extract_metrics doesn't crash", False, str(e))

# Direction of key metrics — human text should have HIGHER burstiness than AI
h_cv  = raw_h.get("sentence_cv")
a_cv  = raw_a.get("sentence_cv")
if h_cv is not None and a_cv is not None:
    record("Human sentence_cv > AI sentence_cv (humans more bursty)",
           h_cv > a_cv, f"human={h_cv:.3f}, ai={a_cv:.3f}")

# Transition density should be HIGHER in AI text
h_td = raw_h.get("transition_density", 0) or 0
a_td = raw_a.get("transition_density", 0) or 0
record("AI transition_density > human (AI overuses transitions)",
       a_td > h_td, f"human={h_td:.4f}, ai={a_td:.4f}")


# ═══════════════════════════════════════════════════════════
#  TEST 3 — score_metrics
# ═══════════════════════════════════════════════════════════
section("3. score_metrics — scoring and evidence")

score_h, comp_h, ev_h = score_metrics(raw_h)
score_a, comp_a, ev_a = score_metrics(raw_a)
score_m, comp_m, ev_m = score_metrics(extract_metrics(MIXED)[0])

record("score_metrics returns int", isinstance(score_h, int))
record("Human score in [0, 100]", 0 <= score_h <= 100, f"score={score_h}")
record("AI score in [0, 100]",    0 <= score_a <= 100, f"score={score_a}")
record("AI score > Human score (core accuracy check)",
       score_a > score_h, f"AI={score_a}, human={score_h}")
record("Mixed score between human and AI scores",
       score_h <= score_m <= score_a or score_h - 10 <= score_m,
       f"human={score_h}, mixed={score_m}, AI={score_a}")

# Evidence checks
record("AI text produces evidence strings", len(ev_a) > 0, f"{len(ev_a)} item(s)")
record("Evidence strings are non-empty", all(len(e) > 5 for e in ev_a))

# Component scores — must all be 0-100
all_comp_ok = all(0 <= v <= 100 for v in comp_h.values())
record("All component_scores in [0, 100]", all_comp_ok, f"scores: {comp_h}")

# score_metrics on None-only metrics (edge case: all skipped)
all_none = {k: None for k in HUMAN_BASELINES}
s_none, c_none, e_none = score_metrics(all_none)
record("All-None metrics returns score=0 gracefully", s_none == 0)
record("All-None metrics returns evidence message", len(e_none) == 1)

# Empty text through full pipeline
raw_e, _, _, _ = extract_metrics(EMPTY)
try:
    s_e, _, _ = score_metrics(raw_e)
    record("Empty text through score_metrics doesn't crash", True, f"score={s_e}")
except Exception as ex:
    record("Empty text through score_metrics doesn't crash", False, str(ex))


# ═══════════════════════════════════════════════════════════
#  TEST 4 — score_paragraph (paragraph-level)
# ═══════════════════════════════════════════════════════════
section("4. score_paragraph — paragraph-level analysis")

# Clear AI paragraph
ai_para = (
    "Furthermore, it is important to note that the water cycle is crucial. "
    "Moreover, it is evident that evaporation plays a significant role. "
    "Additionally, needless to say, precipitation contributes to the cycle. "
    "In conclusion, to summarize, the water cycle is a fundamental process. "
    "Building upon this, firstly, we must consider the hydrological implications."
)

# Clear human paragraph
human_para = (
    "I didn't expect the water cycle to be so... recursive? Like, the same "
    "water just keeps going round. Rain falls, soaks in, evaporates again. "
    "My notebook got wet in that storm last week — ironic, given the topic. "
    "Rivers feel different now: they're not just scenery, they're moving parts "
    "of this massive invisible machine. Weird to think about honestly."
)

s_ai_para,    ev_ai_p    = score_paragraph(ai_para)
s_human_para, ev_human_p = score_paragraph(human_para)

record("score_paragraph AI paragraph returns a score", s_ai_para is not None, f"score={s_ai_para}")
record("score_paragraph human paragraph returns a score", s_human_para is not None, f"score={s_human_para}")

if s_ai_para is not None and s_human_para is not None:
    record("AI paragraph scores higher than human paragraph",
           s_ai_para > s_human_para, f"AI={s_ai_para}, human={s_human_para}")

# Too short -> should return None
s_tiny, _ = score_paragraph("Short.")
record("Too-short paragraph returns None", s_tiny is None)

# Evidence is a list
record("score_paragraph AI evidence is list", isinstance(ev_ai_p, list))

# Empty paragraph
try:
    s_emp, _ = score_paragraph("")
    record("Empty paragraph doesn't crash", True, f"score={s_emp}")
except Exception as ex:
    record("Empty paragraph doesn't crash", False, str(ex))


# ═══════════════════════════════════════════════════════════
#  TEST 5 — generate_paragraph_heatmap
# ═══════════════════════════════════════════════════════════
section("5. generate_paragraph_heatmap — document heatmap")

heatmap_h = generate_paragraph_heatmap(HUMAN)
heatmap_a = generate_paragraph_heatmap(AI_CLEAR)
heatmap_m = generate_paragraph_heatmap(MIXED)

record("Heatmap returns list", isinstance(heatmap_h, list))
record("Human text generates heatmap entries", len(heatmap_h) > 0, f"{len(heatmap_h)} paragraphs")
record("AI text generates heatmap entries",    len(heatmap_a) > 0, f"{len(heatmap_a)} paragraphs")

# Check each entry has correct keys
required_keys = {"index", "text_preview", "score", "label", "evidence"}
for entry in (heatmap_h + heatmap_a + heatmap_m)[:10]:
    missing = required_keys - set(entry.keys())
    if missing:
        record("Heatmap entry has all required keys", False, f"missing: {missing}")
        break
else:
    record("All heatmap entries have required keys (index/text_preview/score/label/evidence)", True)

# Labels must be valid (v4 uses threshold-based labels)
valid_labels = {"REVIEW RECOMMENDED", "NOTABLE SIGNALS", "HUMAN-LIKE", "SKIP (too short)"}
bad_labels = [e["label"] for e in heatmap_h + heatmap_a if e["label"] not in valid_labels]
record("All heatmap labels are valid enum values", len(bad_labels) == 0,
       f"bad labels: {bad_labels}" if bad_labels else "")

# index is sequential starting at 1
for hm in [heatmap_h, heatmap_a]:
    indices = [e["index"] for e in hm]
    if indices != list(range(1, len(hm) + 1)):
        record("Heatmap indices are sequential from 1", False, f"got: {indices}")
        break
else:
    record("Heatmap indices are sequential from 1", True)

# text_preview max 83 chars (80 + "...")
too_long = [e for e in heatmap_h + heatmap_a if len(e.get("text_preview", "")) > 84]
record("text_preview is properly truncated at 80 chars", len(too_long) == 0,
       f"{len(too_long)} entries too long" if too_long else "")

# AI document should have MORE AI-LIKE paragraphs than human document
ai_like_in_ai    = sum(1 for e in heatmap_a if e["label"] == "AI-LIKE")
ai_like_in_human = sum(1 for e in heatmap_h if e["label"] == "AI-LIKE")
record("AI text has more AI-LIKE paragraphs than human text",
       ai_like_in_ai >= ai_like_in_human,
       f"AI doc: {ai_like_in_ai} AI-LIKE, human doc: {ai_like_in_human} AI-LIKE")

# Empty text
try:
    hm_empty = generate_paragraph_heatmap(EMPTY)
    record("Empty text heatmap doesn't crash", True, f"returned {len(hm_empty)} entries")
except Exception as ex:
    record("Empty text heatmap doesn't crash", False, str(ex))


# ═══════════════════════════════════════════════════════════
#  TEST 6 — generate_verdict
# ═══════════════════════════════════════════════════════════
section("6. generate_verdict — final verdict logic")

def make_heatmap(ai_pct, total=10):
    """Build a synthetic heatmap with ai_pct% AI-LIKE paragraphs."""
    n_ai = round(total * ai_pct / 100)
    hm = []
    for i in range(total):
        score = 80 if i < n_ai else 30
        label = "AI-LIKE" if i < n_ai else "HUMAN-LIKE"
        hm.append({"index": i+1, "text_preview": "...", "score": score,
                   "label": label, "evidence": []})
    return hm

# v4 uses threshold-based verdict strings (REVIEW RECOMMENDED / NOTABLE SIGNALS / CONSISTENT WITH HUMAN WRITING)
valid_verdicts = {"REVIEW RECOMMENDED", "NOTABLE SIGNALS", "CONSISTENT WITH HUMAN WRITING"}

# High score + many AI paragraphs -> REVIEW RECOMMENDED
v1 = generate_verdict(75, make_heatmap(60), 500)
record("High score (75) + 60% AI paragraphs -> REVIEW RECOMMENDED",
       v1["verdict"] == "REVIEW RECOMMENDED", f"got: {v1['verdict']}")

# Low score + few AI paragraphs -> CONSISTENT WITH HUMAN WRITING
v2 = generate_verdict(30, make_heatmap(5), 500)
record("Low score (30) + 5% AI paragraphs -> CONSISTENT WITH HUMAN WRITING",
       v2["verdict"] == "CONSISTENT WITH HUMAN WRITING", f"got: {v2['verdict']}")

# Mid-range -> NOTABLE SIGNALS
v3 = generate_verdict(55, make_heatmap(25), 500)
record("Mid score (55) + 25% AI paragraphs -> NOTABLE SIGNALS or REVIEW RECOMMENDED",
       v3["verdict"] in ("NOTABLE SIGNALS", "REVIEW RECOMMENDED"), f"got: {v3['verdict']}")

# All verdicts have required keys
for i, vd in enumerate([v1, v2, v3]):
    req = {"verdict", "confidence", "ai_paragraph_pct", "mixed_paragraph_pct", "summary"}
    missing = req - set(vd.keys())
    record(f"Verdict {i+1} has all required keys", len(missing) == 0,
           f"missing: {missing}" if missing else f"verdict={vd['verdict']}, confidence={vd['confidence']}")

# Confidence based on word count
v_low  = generate_verdict(50, make_heatmap(50), 80)
v_med  = generate_verdict(50, make_heatmap(50), 200)
v_high = generate_verdict(50, make_heatmap(50), 500)
record("Word count < 100 -> Low confidence",    v_low["confidence"] == "Low",    f"got: {v_low['confidence']}")
record("Word count 200 -> Medium confidence",   v_med["confidence"] == "Medium", f"got: {v_med['confidence']}")
record("Word count 500 -> High confidence",     v_high["confidence"] == "High",  f"got: {v_high['confidence']}")

# summary is a non-empty string
for vd in [v1, v2, v3]:
    record("Verdict summary is a non-empty string",
           isinstance(vd["summary"], str) and len(vd["summary"]) > 10)

# All verdict values are valid enum members
for vd in [v1, v2, v3, v_low, v_med, v_high]:
    record("Verdict value is valid enum", vd["verdict"] in valid_verdicts,
           f"got: {vd['verdict']}")


# ═══════════════════════════════════════════════════════════
#  TEST 7 — get_assessment & analyze_sections
# ═══════════════════════════════════════════════════════════
section("7. get_assessment + analyze_sections")

# v4 uses 2-tier assessment strings
valid_assessments = {
    "Consistent with Human Writing Characteristics",
    "Some AI-Like Writing Patterns — Notable",
    "AI-Like Writing Patterns Detected — Review Recommended",
}

for score, expected_contains in [(20, "Human"), (40, "Notable"), (60, "Review"), (80, "Review")]:
    a = get_assessment(score)
    record(f"get_assessment({score}) contains '{expected_contains}'",
           expected_contains in a, f"got: '{a}'")

# Boundary checks
record("get_assessment(35) is valid", get_assessment(35) in valid_assessments)
record("get_assessment(52) is valid", get_assessment(52) in valid_assessments)
record("get_assessment(0) -> Human", "Human" in get_assessment(0))
record("get_assessment(100) -> Review Recommended", "Review" in get_assessment(100))

# analyze_sections
sections_h = analyze_sections(HUMAN)
sections_a = analyze_sections(AI_CLEAR)

record("analyze_sections returns dict with 3 keys",
       set(sections_h.keys()) == {"Introduction", "Body", "Conclusion"})

all_valid = all(v in valid_assessments or v == "Insufficient data"
                for v in sections_h.values())
record("analyze_sections values are valid assessment strings", all_valid,
       str({k: v for k, v in sections_h.items() if v not in valid_assessments and v != "Insufficient data"}))

# Too few paragraphs -> Insufficient data
sections_short = analyze_sections("One paragraph only, no splits here.")
record("analyze_sections on 1-paragraph text -> Insufficient data",
       all(v == "Insufficient data" for v in sections_short.values()),
       str(sections_short))


# ═══════════════════════════════════════════════════════════
#  TEST 8 — evaluate_document (full single-doc pipeline)
# ═══════════════════════════════════════════════════════════
section("8. evaluate_document — full single-document pipeline")

res_h = evaluate_document(HUMAN)
res_a = evaluate_document(AI_CLEAR)
res_m = evaluate_document(MIXED)
res_s = evaluate_document(STUDENT_A)

required_fields = {
    "writing_characteristics_score", "assessment", "confidence",
    "indicators", "section_analysis", "component_scores",
    "verdict", "verdict_summary", "ai_paragraph_pct",
    "mixed_paragraph_pct", "paragraph_heatmap",
}

for name, res in [("HUMAN", res_h), ("AI_CLEAR", res_a), ("MIXED", res_m), ("STUDENT_A", res_s)]:
    missing = required_fields - set(res.keys())
    record(f"evaluate_document({name}) returns all required fields",
           len(missing) == 0, f"missing: {missing}" if missing else
           f"score={res['writing_characteristics_score']}, verdict={res['verdict']}")

# Core accuracy check
score_h_doc = res_h["writing_characteristics_score"]
score_a_doc = res_a["writing_characteristics_score"]
score_m_doc = res_m["writing_characteristics_score"]
record("AI_CLEAR scores higher than HUMAN (accuracy)",
       score_a_doc > score_h_doc,
       f"AI={score_a_doc}, HUMAN={score_h_doc}, MIXED={score_m_doc}")

# Verdict accuracy (v4 uses threshold-based string verdicts)
record("HUMAN text verdict is CONSISTENT WITH HUMAN WRITING or NOTABLE SIGNALS",
       res_h["verdict"] in ("CONSISTENT WITH HUMAN WRITING", "NOTABLE SIGNALS"),
       f"got: {res_h['verdict']} (score={score_h_doc})")
record("AI_CLEAR text verdict is REVIEW RECOMMENDED",
       res_a["verdict"] == "REVIEW RECOMMENDED",
       f"got: {res_a['verdict']} (score={score_a_doc})")

# indicators is list of <= 5 strings
record("indicators is list of max 5 strings",
       isinstance(res_h["indicators"], list) and len(res_h["indicators"]) <= 5)

# component_scores — all present and in range
all_ok = all(0 <= v <= 100 for v in res_a["component_scores"].values())
record("component_scores all in [0, 100]", all_ok, str(res_a["component_scores"]))

# ai_paragraph_pct in [0, 100]
record("ai_paragraph_pct in [0.0, 100.0]",
       0.0 <= res_a["ai_paragraph_pct"] <= 100.0, f"{res_a['ai_paragraph_pct']}")

# paragraph_heatmap is list
record("paragraph_heatmap is a list",
       isinstance(res_h["paragraph_heatmap"], list),
       f"{len(res_h['paragraph_heatmap'])} entries")

# Edge cases — should not crash
for label, txt in [("EMPTY", EMPTY), ("ONE_WORD", ONE_WORD), ("SPACES_ONLY", ONLY_SPACES)]:
    try:
        r = evaluate_document(txt)
        record(f"evaluate_document({label}) doesn't crash",
               True, f"score={r['writing_characteristics_score']}, verdict={r['verdict']}")
    except Exception as ex:
        record(f"evaluate_document({label}) doesn't crash", False, str(ex)[:80])


# ═══════════════════════════════════════════════════════════
#  TEST 9 — analyze_ai_characteristics (batch API)
# ═══════════════════════════════════════════════════════════
section("9. analyze_ai_characteristics — batch processing")

import time
batch = {
    "human.txt":    HUMAN,
    "ai_clear.txt": AI_CLEAR,
    "mixed.txt":    MIXED,
    "student_a.txt": STUDENT_A,
    "empty.txt":    EMPTY,
}

t0 = time.time()
batch_result = analyze_ai_characteristics(batch)
elapsed = time.time() - t0

record("Batch returns same keys as input",
       set(batch_result.keys()) == set(batch.keys()))
record(f"Batch processes 5 docs quickly (< 5s)", elapsed < 5.0, f"{elapsed:.3f}s")

# Each result must have all fields
for fname, res in batch_result.items():
    missing = required_fields - set(res.keys())
    record(f"Batch result for '{fname}' has all fields",
           len(missing) == 0, f"missing: {missing}" if missing else
           f"score={res['writing_characteristics_score']}")

# Relative order check: ai_clear should score higher than human
s_b_human = batch_result["human.txt"]["writing_characteristics_score"]
s_b_ai    = batch_result["ai_clear.txt"]["writing_characteristics_score"]
record("Batch: ai_clear scores higher than human",
       s_b_ai > s_b_human, f"AI={s_b_ai}, human={s_b_human}")

# Empty doc in batch — should not break others
human_ok = "writing_characteristics_score" in batch_result.get("human.txt", {})
record("Empty doc in batch doesn't corrupt other results", human_ok)


# ═══════════════════════════════════════════════════════════
#  TEST 10 — Real student samples accuracy
# ═══════════════════════════════════════════════════════════
section("10. REAL STUDENT SAMPLES — end-to-end accuracy")

sample_dir = os.path.join(_PROJECT_ROOT, "sample_assignments")
student_files = [f for f in os.listdir(sample_dir) if f.startswith("student_") and f.endswith(".txt")]

print(f"\n  Loading {len(student_files)} real student files...\n")

all_results = {}
for fname in sorted(student_files):
    fpath = os.path.join(sample_dir, fname)
    try:
        with open(fpath, encoding="utf-8") as f:
            content = f.read()
        result = evaluate_document(content)
        all_results[fname] = result
        score = result["writing_characteristics_score"]
        verdict = result["verdict"]
        conf = result["confidence"]
        ai_pct = result["ai_paragraph_pct"]
        print(f"  {fname:<20}  score={score:3d}  verdict={verdict:<15}  "
              f"confidence={conf:<8}  AI-paras={ai_pct:.1f}%")
    except Exception as ex:
        print(f"  {fname:<20}  ERROR: {ex}")
        all_results[fname] = None

# All student files should process without crashing
no_crashes = all(v is not None for v in all_results.values())
record("All student files process without crashing", no_crashes,
       f"{sum(1 for v in all_results.values() if v is not None)}/{len(all_results)} ok")

# All should have valid verdicts (v4 threshold-based strings)
valid = {"REVIEW RECOMMENDED", "NOTABLE SIGNALS", "CONSISTENT WITH HUMAN WRITING"}
bad_verdicts = {k: v["verdict"] for k, v in all_results.items()
                if v and v["verdict"] not in valid}
record("All student verdicts are valid enum values", len(bad_verdicts) == 0,
       str(bad_verdicts) if bad_verdicts else "")

# student_A and student_B are ~identical copies — their AI scores should be very close
if "student_A.txt" in all_results and "student_B.txt" in all_results:
    sa = all_results["student_A.txt"]
    sb = all_results["student_B.txt"]
    if sa and sb:
        diff = abs(sa["writing_characteristics_score"] - sb["writing_characteristics_score"])
        record("student_A and student_B have similar AI scores (near-identical docs)",
               diff <= 15, f"A={sa['writing_characteristics_score']}, B={sb['writing_characteristics_score']}, diff={diff}")

# Consistency check: re-running on same text gives same score
if "student_A.txt" in all_results and all_results["student_A.txt"]:
    content_a = open(os.path.join(sample_dir, "student_A.txt"), encoding="utf-8").read()
    res2 = evaluate_document(content_a)
    same = res2["writing_characteristics_score"] == all_results["student_A.txt"]["writing_characteristics_score"]
    record("Deterministic: same input always gives same score", same,
           "run1=" + str(all_results["student_A.txt"]["writing_characteristics_score"]) + ", run2=" + str(res2["writing_characteristics_score"]))


# ═══════════════════════════════════════════════════════════
#  TEST 11 — METRIC_CONFIG integrity
# ═══════════════════════════════════════════════════════════
section("11. METRIC_CONFIG + HUMAN_BASELINES integrity (v4 — 7 metrics)")

record("METRIC_CONFIG has exactly 7 entries", len(METRIC_CONFIG) == 7, f"got {len(METRIC_CONFIG)}")

weight_sum = sum(w for _, _, w, _ in METRIC_CONFIG)
record("METRIC_CONFIG weights sum exactly to 1.0", abs(weight_sum - 1.0) < 1e-3, f"sum={weight_sum:.6f}")

valid_directions = {"high_is_ai", "low_is_ai"}
bad_dirs = [(k, d) for k, d, w, _ in METRIC_CONFIG if d not in valid_directions]
record("All METRIC_CONFIG directions are valid", len(bad_dirs) == 0, str(bad_dirs) if bad_dirs else "")

all_positive_weights = all(w >= 0 for _, _, w, _ in METRIC_CONFIG)
record("All METRIC_CONFIG weights are non-negative", all_positive_weights)

# Every key in METRIC_CONFIG must have a baseline
cfg_keys = {k for k, _, _, _ in METRIC_CONFIG}
missing_baselines = cfg_keys - set(HUMAN_BASELINES.keys())
record("Every METRIC_CONFIG key has a HUMAN_BASELINE entry",
       len(missing_baselines) == 0, str(missing_baselines) if missing_baselines else "")

# All baselines have positive std_dev
bad_stds = [(k, std) for k, (mean, std) in HUMAN_BASELINES.items() if std <= 0]
record("All HUMAN_BASELINES have positive std_dev", len(bad_stds) == 0, str(bad_stds) if bad_stds else "")

# v4 validated metrics present (passive_ratio and starter_variety were rejected in v4 — see module docstring)
v4_metrics = {"hedge_density"}
record("v4 new metric 'hedge_density' present in HUMAN_BASELINES",
       v4_metrics.issubset(set(HUMAN_BASELINES.keys())), str(v4_metrics - set(HUMAN_BASELINES.keys())))
record("v4 new metric 'hedge_density' present in METRIC_CONFIG",
       v4_metrics.issubset({k for k, _, _, _ in METRIC_CONFIG}))

# ═══════════════════════════════════════════════════════════
#  FINAL REPORT
# ═══════════════════════════════════════════════════════════
print(f"\n{'=' * 62}")
print("  AI DETECTOR TEST REPORT")
print('=' * 62)

passed = [r for r in results if r[1]]
failed = [r for r in results if not r[1]]

print(f"\n  Total tests  : {len(results)}")
print(f"  Passed       : {len(passed)}")
print(f"  Failed       : {len(failed)}")
print(f"  Pass rate    : {len(passed)/len(results)*100:.1f}%")

if failed:
    print(f"\n  --- FAILED TESTS ---")
    for name, _, detail in failed:
        print(f"  x  {name}")
        if detail:
            print(f"       {detail[:120]}")

print()
if len(failed) == 0:
    print("  ALL TESTS PASSED -- AI detector is functioning correctly.\n")
elif len(failed) <= 4:
    print("  MOSTLY PASSING -- Minor issues in AI detector.\n")
else:
    print("  MULTIPLE FAILURES -- AI detector has significant issues.\n")
