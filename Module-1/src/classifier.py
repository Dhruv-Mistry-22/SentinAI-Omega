"""
classifier.py — Document classification and WHO-copied-WHOM detection.

Classifies every document pair into:
  COPIED      (combined score >= 0.85)
  SUSPICIOUS  (0.50 – 0.84)
  ORIGINAL    (< 0.50)

For COPIED / SUSPICIOUS pairs, uses file-system timestamps
and PDF metadata to determine the *likely original author*.
"""


# ────────────────────── THRESHOLDS ──────────────────────

THRESHOLD_COPIED = 0.85
THRESHOLD_SUSPICIOUS = 0.50


# ────────────────────── PAIR CLASSIFICATION ──────────────────────

def classify_score(score):
    """Map a combined similarity score to a status string."""
    if score >= THRESHOLD_COPIED:
        return "COPIED"
    if score >= THRESHOLD_SUSPICIOUS:
        return "SUSPICIOUS"
    return "ORIGINAL"


# ────────────────────── AUTHORSHIP ──────────────────────

def determine_original(doc1, doc2):
    """
    Determine which file is the likely *original* when two are flagged.

    Heuristics (cumulative scoring):
      +2  earlier modification time
      +1  earlier creation time
      +1  PDF author field mismatch insight

    Returns ``{original, copier, reason}``.
    """
    m1 = doc1["metadata"]
    m2 = doc2["metadata"]

    score1 = 0          # positive → doc1 is original
    reasons = []

    # ── Modification time ──
    t1, t2 = m1.get("modified_time", 0), m2.get("modified_time", 0)
    if t1 and t2 and t1 != t2:
        diff_h = abs(t1 - t2) / 3600
        if t1 < t2:
            score1 += 2
            reasons.append(
                f"{doc1['filename']} modified {diff_h:.1f}h earlier"
            )
        else:
            score1 -= 2
            reasons.append(
                f"{doc2['filename']} modified {diff_h:.1f}h earlier"
            )

    # ── Creation time ──
    c1, c2 = m1.get("created_time", 0), m2.get("created_time", 0)
    if c1 and c2 and c1 != c2:
        if c1 < c2:
            score1 += 1
            reasons.append(f"{doc1['filename']} created first")
        else:
            score1 -= 1
            reasons.append(f"{doc2['filename']} created first")

    # ── PDF author field ──
    a1 = m1.get("pdf_author")
    a2 = m2.get("pdf_author")
    if a1 and a2 and a1 == a2:
        reasons.append(f"Both PDFs share author field: '{a1}'")

    # ── Decision ──
    if score1 > 0:
        orig, copi = doc1["filename"], doc2["filename"]
    elif score1 < 0:
        orig, copi = doc2["filename"], doc1["filename"]
    else:
        # Tie-break alphabetically
        orig, copi = sorted([doc1["filename"], doc2["filename"]])
        reasons.append("Timestamps identical — listed alphabetically")

    return {
        "original": orig,
        "copier": copi,
        "reason": "; ".join(reasons) if reasons else "Based on file timestamps",
    }


# ────────────────────── BULK CLASSIFICATION ──────────────────────

def classify_all_pairs(analysis_result, documents):
    """
    Classify every pair and return only COPIED / SUSPICIOUS ones.

    Returns a **sorted** list of dicts (highest score first).
    """
    files = analysis_result["files"]
    combined = analysis_result["combined_matrix"]
    tfidf = analysis_result["tfidf_matrix"]
    jaccard = analysis_result["jaccard_matrix"]
    structural = analysis_result["structural_matrix"]
    style = analysis_result["style_matrix"]

    doc_by_name = {d["filename"]: d for d in documents}
    flagged = []

    n = len(files)
    for i in range(n):
        for j in range(i + 1, n):
            score = combined[i][j]
            cls = classify_score(score)

            if cls not in ("COPIED", "SUSPICIOUS"):
                continue

            d1 = doc_by_name.get(files[i])
            d2 = doc_by_name.get(files[j])

            if d1 and d2:
                auth = determine_original(d1, d2)
            else:
                auth = {
                    "original": files[i],
                    "copier": files[j],
                    "reason": "Metadata unavailable",
                }

            flagged.append({
                "file1": files[i],
                "file2": files[j],
                "combined_score": float(score),
                "tfidf_score": float(tfidf[i][j]),
                "jaccard_score": float(jaccard[i][j]),
                "structural_score": float(structural[i][j]),
                "style_score": float(style[i][j]),
                "classification": cls,
                "original": auth["original"],
                "copier": auth["copier"],
                "reason": auth["reason"],
            })

    flagged.sort(key=lambda x: x["combined_score"], reverse=True)
    return flagged


# ────────────────────── PER-DOCUMENT VERDICTS ──────────────────────

def get_document_verdicts(files, flagged_pairs):
    """
    Roll up pair-level classifications into a per-document verdict.

    Returns ``{filename: {status, copied_from, max_score, details}}``.
    """
    verdicts = {
        f: {"status": "ORIGINAL", "copied_from": None,
            "max_score": 0.0, "details": []}
        for f in files
    }

    for p in flagged_pairs:
        copier = p["copier"]
        original = p["original"]
        score = p["combined_score"]
        cls = p["classification"]

        # Escalate the copier's status
        if cls == "COPIED" and verdicts[copier]["status"] != "COPIED":
            verdicts[copier]["status"] = "COPIED"
            verdicts[copier]["copied_from"] = original
        elif cls == "SUSPICIOUS" and verdicts[copier]["status"] == "ORIGINAL":
            verdicts[copier]["status"] = "SUSPICIOUS"
            verdicts[copier]["copied_from"] = original

        verdicts[copier]["max_score"] = max(verdicts[copier]["max_score"], score)
        verdicts[copier]["details"].append(
            f"{score:.2f} vs {original} ({cls})"
        )

        # Annotate the original as well (informational)
        verdicts[original]["details"].append(
            f"{score:.2f} vs {copier} ({cls}) — this doc is likely original"
        )

    return verdicts
