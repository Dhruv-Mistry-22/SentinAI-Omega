"""
ai_detector.py — AI Writing Characteristics Analyzer (v4)

v4 = v3 (recalibrated 6-metric core) + hedge_density (validated new signal)

What changed from v3 → v4:
  ADDED:
    - hedge_density: detects AI over-hedging ("it is important to note",
      "arguably", "presumably", etc.) Tested clean separation:
      AI ~0.22-0.27, Human ~0.0, Wikipedia ~0.0.

  REJECTED (tested against real + synthetic AI/human/Wikipedia samples,
  did not make the cut — see CALIBRATION_NOTES.md for the test data):
    - passive_ratio: Wikipedia scores nearly as high as AI on this metric
      (0.43-0.50 vs 0.46-0.56). Including it reintroduces false positives
      on formal/encyclopedic human writing — the exact problem v3 fixed.
    - starter_variety: showed no discrimination at all between AI (0.82-0.89),
      human (0.83-1.0), and Wikipedia (0.86-1.0) in testing. Either needs
      much longer documents or the underlying assumption doesn't hold at
      typical assignment length.

  BUG FIX: the previous draft had "it is important to note" listed in BOTH
  the transition-phrase list and the hedge-phrase list, double-counting
  that phrase across two metrics and inflating scores. Removed the
  overlapping phrases from the transition list.

Real test data used for calibration (see CALIBRATION_NOTES.md):
  AI student (confirmed)   → 78%  (was 73% in v3)
  Human student (confirmed)→ 19%  (was 18% in v3)
  Wikipedia (human)        → 35%  (was 37% in v3)
"""

import re
import math
from collections import Counter
from .utils import progress_bar


# ═══════════════════════════════════════════════════════════════════════
#  HUMAN BASELINE STATISTICS
#  (mean, std_dev) for each metric, based on typical student academic
#  writing AND tested against AI-generated and Wikipedia-style text to
#  confirm discrimination. Only metrics that showed clean separation
#  in testing are kept (7 of the original 13 candidates).
# ═══════════════════════════════════════════════════════════════════════

HUMAN_BASELINES = {
    # CV of sentence char lengths. Human = bursty (high CV). AI = uniform (low CV).
    "sentence_cv":        (0.55, 0.15),

    # CV of sentence word counts. Same logic.
    "word_cv":            (0.50, 0.14),

    # AI transition phrase density. AI overuses "Furthermore", "In conclusion" etc.
    # Human baseline: ~0.04. Wikipedia: ~0.02 (encyclopedic, not argumentative).
    # AI: ~0.30+ (tested).
    "transition_density": (0.04, 0.04),

    # CV of paragraph char lengths. AI writes very uniform paragraphs.
    "paragraph_cv":       (0.65, 0.20),

    # Bigram repetition ratio. Slightly raised baseline — encyclopedic
    # text legitimately repeats domain terms more than conversational writing.
    "repetition_ratio":   (0.07, 0.04),

    # CV of punctuation counts per paragraph.
    "punct_cv":           (0.70, 0.22),

    # NEW in v4 — Hedge word density (hedge phrases per sentence).
    # AI overuses hedging language far more than students or Wikipedia.
    # Tested: Human ~0.00, Wikipedia ~0.00, AI ~0.22-0.27.
    # Baseline set conservatively low so any real hedging usage is caught.
    "hedge_density":      (0.015, 0.02),
}


def z_score(value, key):
    """Z-score relative to human baseline. Positive = higher than human mean."""
    mean, std = HUMAN_BASELINES[key]
    if std == 0:
        return 0.0
    return (value - mean) / std


def z_to_ai_probability(z, direction="high_is_ai"):
    """
    Sigmoid conversion of Z-score to AI probability (0.0-1.0).
    k=1.5 steepness: Z=0 → 50%, Z=±2 → ~95%/~5%.
    """
    if direction == "low_is_ai":
        z = -z
    k = 1.5
    return 1.0 / (1.0 + math.exp(-k * z))


# ═══════════════════════════════════════════════════════════════════════
#  PHRASE LISTS
#  IMPORTANT: hedge phrases and transition phrases must NOT overlap.
#  A prior draft had "it is important to note" in both lists, which
#  double-counted that phrase across two metrics. Fixed here.
# ═══════════════════════════════════════════════════════════════════════

_HEDGE_PHRASES = [
    "it is important to note", "it is worth noting", "it should be noted",
    "it is crucial to", "one might argue", "it can be argued",
    "it is generally accepted", "it is widely believed",
    "it is often said", "it is commonly known", "it is clear that",
    "it is evident that", "it is apparent that", "it is obvious that",
    "it is reasonable to", "it is possible that", "it could be said",
    "it may be argued", "it appears that", "it seems that",
    "arguably", "presumably", "supposedly", "ostensibly",
]
_COMPILED_HEDGES = [re.compile(r'\b' + re.escape(p) + r'\b', re.IGNORECASE)
                    for p in _HEDGE_PHRASES]

# Transition phrases — overlapping entries with the hedge list removed:
# "it is important to note", "it is worth noting", "it is evident",
# "crucial to understand" (overlaps "it is crucial to") were removed.
_AI_TRANSITIONS = [
    "in conclusion", "furthermore", "moreover", "additionally",
    "firstly", "secondly", "thirdly",
    "ultimately", "on the other hand", "to summarize", "in essence",
    "as a result", "consequently", "delve into", "a testament to",
    "in summary", "to begin with", "building upon", "in light of",
    "having said that", "needless to say", "as previously mentioned",
]
_COMPILED_TRANSITIONS = [re.compile(r'\b' + re.escape(p) + r'\b', re.IGNORECASE)
                         for p in _AI_TRANSITIONS]


# ═══════════════════════════════════════════════════════════════════════
#  METRIC WEIGHTS
#  Calibrated against confirmed AI text, confirmed human text, and
#  Wikipedia (human encyclopedic) text. transition_density and
#  hedge_density carry the most weight — they showed the cleanest
#  separation in testing.
# ═══════════════════════════════════════════════════════════════════════

METRIC_CONFIG = [
    ("sentence_cv",        "low_is_ai",  0.18, "Sentence length uniformity"),
    ("word_cv",            "low_is_ai",  0.16, "Word-count burstiness"),
    ("transition_density", "high_is_ai", 0.27, "AI transition phrase density"),
    ("paragraph_cv",       "low_is_ai",  0.13, "Paragraph structure uniformity"),
    ("repetition_ratio",   "high_is_ai", 0.02, "Phrase repetition ratio"),
    ("punct_cv",           "low_is_ai",  0.06, "Punctuation consistency"),
    ("hedge_density",      "high_is_ai", 0.18, "Hedge word density"),
]

assert abs(sum(w for _, _, w, _ in METRIC_CONFIG) - 1.0) < 0.001


# ═══════════════════════════════════════════════════════════════════════
#  THRESHOLDS
#  Calibrated against real + tested data:
#    Confirmed human → 19%   Wikipedia → 35%   Confirmed AI → 78%
# ═══════════════════════════════════════════════════════════════════════

THRESHOLD_REVIEW  = 55   # >= this → REVIEW RECOMMENDED
THRESHOLD_NOTABLE = 35   # >= this → NOTABLE SIGNALS
                          # <  this → CONSISTENT HUMAN WRITING

def get_assessment(score):
    if score >= THRESHOLD_REVIEW:
        return "AI-Like Writing Patterns Detected — Review Recommended"
    if score >= THRESHOLD_NOTABLE:
        return "Some AI-Like Writing Patterns — Notable"
    return "Consistent with Human Writing Characteristics"


# ═══════════════════════════════════════════════════════════════════════
#  CORE HELPERS
# ═══════════════════════════════════════════════════════════════════════

def _cv(values):
    n = len(values)
    if n < 2:
        return 0.0
    avg = sum(values) / n
    if avg == 0:
        return 0.0
    variance = sum((v - avg) ** 2 for v in values) / n
    return math.sqrt(variance) / avg


# ═══════════════════════════════════════════════════════════════════════
#  METRIC EXTRACTION
# ═══════════════════════════════════════════════════════════════════════

def extract_metrics(text):
    """
    Extracts the 7 active metric values from a text block.
    Returns ({metric_key: value_or_None}, sentences, words, paragraphs).
    """
    sentences  = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text.strip())
                  if len(s.split()) >= 3]
    words      = re.findall(r"\b\w+\b", text.lower())
    paragraphs = [p.strip() for p in text.split("\n\n") if len(p.strip()) > 20]

    metrics = {}

    # 1. Sentence uniformity (char lengths)
    metrics["sentence_cv"] = _cv([len(s) for s in sentences]) if len(sentences) >= 3 else None

    # 2. Burstiness (word counts per sentence)
    metrics["word_cv"] = _cv([len(s.split()) for s in sentences]) if len(sentences) >= 3 else None

    # 3. Transition phrase density
    if len(sentences) >= 2:
        count = sum(len(p.findall(text)) for p in _COMPILED_TRANSITIONS)
        metrics["transition_density"] = count / len(sentences)
    else:
        metrics["transition_density"] = None

    # 4. Paragraph char CV
    metrics["paragraph_cv"] = _cv([len(p) for p in paragraphs]) if len(paragraphs) >= 3 else None

    # 5. Bigram repetition ratio
    if len(words) >= 20:
        bigrams   = [" ".join(words[i:i+2]) for i in range(len(words) - 1)]
        bi_counts = Counter(bigrams)
        repeated  = sum(c for c in bi_counts.values() if c > 2)
        metrics["repetition_ratio"] = repeated / len(words)
    else:
        metrics["repetition_ratio"] = None

    # 6. Punctuation CV across paragraphs
    if len(paragraphs) >= 3:
        punct_counts = [len(re.findall(r'[.,;!?]', p)) for p in paragraphs]
        metrics["punct_cv"] = _cv(punct_counts)
    else:
        metrics["punct_cv"] = None

    # 7. Hedge word density (NEW in v4)
    if len(sentences) >= 2:
        hedge_count = sum(len(p.findall(text)) for p in _COMPILED_HEDGES)
        metrics["hedge_density"] = hedge_count / len(sentences)
    else:
        metrics["hedge_density"] = None

    return metrics, sentences, words, paragraphs


# ═══════════════════════════════════════════════════════════════════════
#  SCORING ENGINE
# ═══════════════════════════════════════════════════════════════════════

def score_metrics(raw_metrics):
    """
    Converts raw metric values → weighted AI probability score (0-100).
    Returns (overall_score, component_probs_dict, evidence_list).
    """
    total_weight, weighted_sum = 0.0, 0.0
    component_probs = {}
    evidence = []

    for key, direction, weight, name in METRIC_CONFIG:
        raw = raw_metrics.get(key)
        if raw is None:
            continue

        z    = z_score(raw, key)
        prob = z_to_ai_probability(z, direction)
        component_probs[key] = round(prob * 100)

        weighted_sum += prob * weight
        total_weight += weight

        if prob > 0.72:
            mean, _ = HUMAN_BASELINES[key]
            if direction == "low_is_ai":
                evidence.append(
                    f"{name}: {raw:.2f} (expected ~{mean:.2f} in human writing — "
                    f"unusually low, suggesting AI uniformity)"
                )
            else:
                evidence.append(
                    f"{name}: {raw:.2f} (expected ~{mean:.2f} in human writing — "
                    f"unusually high, a common AI pattern)"
                )

    if total_weight == 0:
        return 0, {}, ["Insufficient text to analyze."]

    final_score = round((weighted_sum / total_weight) * 100)

    if not evidence:
        evidence.append("No metrics significantly outside normal human writing ranges.")

    return final_score, component_probs, evidence


# ═══════════════════════════════════════════════════════════════════════
#  PARAGRAPH-LEVEL HEATMAP
# ═══════════════════════════════════════════════════════════════════════

def score_paragraph(para_text):
    """
    Scores a single paragraph using sentence-level metrics only.
    Returns (score_0_to_100_or_None, evidence_list).
    """
    PARA_CONFIG = [
        ("sentence_cv",        "low_is_ai",  0.20, "Sentence uniformity"),
        ("word_cv",            "low_is_ai",  0.18, "Burstiness"),
        ("transition_density", "high_is_ai", 0.30, "AI transitions"),
        ("repetition_ratio",   "high_is_ai", 0.05, "Phrase repetition"),
        ("punct_cv",           "low_is_ai",  0.07, "Punctuation consistency"),
        ("hedge_density",      "high_is_ai", 0.20, "Hedge word density"),
    ]

    raw, _, words, _ = extract_metrics(para_text)
    if len(words) < 30:
        return None, []

    sentences = [s for s in re.split(r"(?<=[.!?])\s+", para_text.strip())
                 if len(s.split()) >= 3]
    if len(sentences) < 2:
        return None, []

    total_w, weighted_sum = 0.0, 0.0
    evidence = []

    for key, direction, weight, name in PARA_CONFIG:
        val = raw.get(key)
        if val is None:
            continue
        z    = z_score(val, key)
        prob = z_to_ai_probability(z, direction)
        weighted_sum += prob * weight
        total_w      += weight
        if prob > 0.75:
            evidence.append(name)

    if total_w == 0:
        return None, []

    return round((weighted_sum / total_w) * 100), evidence


def generate_paragraph_heatmap(text):
    """
    Scores every paragraph independently.
    Returns list of dicts with index, preview, score, label, evidence.
    """
    paragraphs = [p.strip() for p in text.split("\n\n") if len(p.strip()) > 20]
    heatmap = []

    for i, para in enumerate(paragraphs):
        score, evidence = score_paragraph(para)

        if score is None:
            label = "SKIP (too short)"
        elif score >= THRESHOLD_REVIEW:
            label = "REVIEW RECOMMENDED"
        elif score >= THRESHOLD_NOTABLE:
            label = "NOTABLE SIGNALS"
        else:
            label = "HUMAN-LIKE"

        heatmap.append({
            "index":        i + 1,
            "text_preview": para[:80] + ("..." if len(para) > 80 else ""),
            "score":        score,
            "label":        label,
            "evidence":     evidence,
        })

    return heatmap


# ═══════════════════════════════════════════════════════════════════════
#  DOCUMENT-LEVEL VERDICT
# ═══════════════════════════════════════════════════════════════════════

def generate_verdict(overall_score, heatmap, word_count):
    """
    Combines overall score + paragraph distribution into an actionable
    verdict. Never claims proof — always frames as "review recommended."
    """
    scorable   = [p for p in heatmap if p["score"] is not None]
    flag_paras = [p for p in scorable if p["score"] >= THRESHOLD_REVIEW]
    note_paras = [p for p in scorable if THRESHOLD_NOTABLE <= p["score"] < THRESHOLD_REVIEW]

    flag_pct = (len(flag_paras) / len(scorable) * 100) if scorable else 0
    note_pct = (len(note_paras) / len(scorable) * 100) if scorable else 0

    if word_count < 100:
        confidence = "Low"
    elif word_count < 350:
        confidence = "Medium"
    else:
        confidence = "High"

    if overall_score >= THRESHOLD_REVIEW and flag_pct >= 30:
        verdict = "REVIEW RECOMMENDED"
        summary = (
            f"AI-like writing patterns detected (score: {overall_score}%). "
            f"{flag_pct:.0f}% of paragraphs flagged for review. "
            f"Recommend manual review and, if necessary, oral examination."
        )
    elif overall_score >= THRESHOLD_NOTABLE or flag_pct >= 20:
        verdict = "NOTABLE SIGNALS"
        summary = (
            f"Some AI-like patterns present (score: {overall_score}%). "
            f"{flag_pct:.0f}% paragraphs flagged, {note_pct:.0f}% notable. "
            f"Could indicate partial AI use, structured writing style, or "
            f"non-native speaker. Manual spot-check recommended."
        )
    else:
        verdict = "CONSISTENT WITH HUMAN WRITING"
        summary = (
            f"Writing patterns consistent with human authorship "
            f"(score: {overall_score}%). No significant AI-like signals."
        )

    return {
        "verdict":             verdict,
        "confidence":          confidence,
        "flagged_para_pct":    round(flag_pct, 1),
        "notable_para_pct":    round(note_pct, 1),
        "summary":             summary,
        "ai_paragraph_pct":    round(flag_pct, 1),     # legacy key
        "mixed_paragraph_pct": round(note_pct, 1),     # legacy key
    }


# ═══════════════════════════════════════════════════════════════════════
#  SECTION-LEVEL ANALYSIS  (Intro / Body / Conclusion)
# ═══════════════════════════════════════════════════════════════════════

def _label_section(score):
    return "Insufficient data" if score is None else get_assessment(score)


def _score_section(text):
    if not text.strip() or len(text.split()) < 40:
        return None
    raw, _, _, _ = extract_metrics(text)
    score, _, _  = score_metrics(raw)
    return score


def analyze_sections(text):
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    if len(paragraphs) < 3:
        return {
            "Introduction": "Insufficient data",
            "Body":         "Insufficient data",
            "Conclusion":   "Insufficient data",
        }

    n         = len(paragraphs)
    intro_end = max(1, int(n * 0.20))
    body_end  = max(intro_end + 1, int(n * 0.80))

    return {
        "Introduction": _label_section(_score_section("\n\n".join(paragraphs[:intro_end]))),
        "Body":         _label_section(_score_section("\n\n".join(paragraphs[intro_end:body_end]))),
        "Conclusion":   _label_section(_score_section("\n\n".join(paragraphs[body_end:]))),
    }


# ═══════════════════════════════════════════════════════════════════════
#  MAIN EVALUATION FUNCTION
# ═══════════════════════════════════════════════════════════════════════

def evaluate_document(text):
    """
    Full analysis of one document.
    Returns a dict backward-compatible with the existing report generator.
    """
    words      = re.findall(r"\b\w+\b", text.lower())
    word_count = len(words)

    raw_metrics, _, _, _          = extract_metrics(text)
    overall_score, comp, evidence = score_metrics(raw_metrics)
    heatmap                       = generate_paragraph_heatmap(text)
    verdict_data                  = generate_verdict(overall_score, heatmap, word_count)
    section_analysis              = analyze_sections(text)

    if word_count < 100:
        confidence = "Low (Text too short)"
    elif word_count < 350:
        confidence = "Medium"
    else:
        confidence = "High"

    return {
        # Backward-compatible fields
        "writing_characteristics_score": overall_score,
        "assessment":                    get_assessment(overall_score),
        "confidence":                    confidence,
        "indicators":                    evidence[:5],
        "section_analysis":              section_analysis,
        "component_scores":              comp,

        # New fields
        "verdict":             verdict_data["verdict"],
        "verdict_summary":     verdict_data["summary"],
        "ai_paragraph_pct":    verdict_data["ai_paragraph_pct"],
        "mixed_paragraph_pct": verdict_data["mixed_paragraph_pct"],
        "paragraph_heatmap":   heatmap,
    }


# ═══════════════════════════════════════════════════════════════════════
#  PUBLIC API
# ═══════════════════════════════════════════════════════════════════════

def analyze_ai_characteristics(raw_texts):
    """
    Main entry point. Drop-in replacement for the original function.
    Accepts {filename: text} dict, returns {filename: result_dict}.
    """
    results   = {}
    filenames = list(raw_texts.keys())

    for i, fname in enumerate(filenames):
        progress_bar(i + 1, len(filenames), "  Characteristics Analysis")
        results[fname] = evaluate_document(raw_texts[fname])

    return results
