"""
sentence_matcher.py — Sentence-level plagiarism evidence.

After the document-level analysis flags a pair as COPIED or
SUSPICIOUS, this module drills down to find *exactly which
sentences* are shared.  The results are included in the PDF
report as concrete evidence.

Uses ``difflib.SequenceMatcher`` (stdlib) for fast, memory-
efficient pairwise sentence comparison.
"""

import re
from difflib import SequenceMatcher


# ────────────────────── SENTENCE SPLITTING ──────────────────────

def split_sentences(text):
    """
    Split *text* into a list of sentences (min 4 words each).
    Uses punctuation-based splitting — much faster than NLTK's
    ``sent_tokenize`` and sufficient for assignment text.
    """
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    return [s.strip() for s in sentences if len(s.split()) >= 4]


# ────────────────────── MATCHING ──────────────────────

def find_matching_sentences(text1, text2, threshold=0.80):
    """
    Find sentences shared between two documents.

    Parameters
    ----------
    text1, text2 : str
        Raw document texts.
    threshold : float
        Minimum SequenceMatcher ratio to flag a pair (0–1).

    Returns
    -------
    list[dict]
        Each dict: ``{sent1, sent2, similarity, line_doc1, line_doc2}``
    """
    sents1 = split_sentences(text1)
    sents2 = split_sentences(text2)

    matches = []
    used_j = set()  # avoid double-matching

    for i, s1 in enumerate(sents1):
        best_match = None
        best_sim = threshold
        best_j = -1

        s1_low = s1.lower().strip()

        for j, s2 in enumerate(sents2):
            if j in used_j:
                continue

            s2_low = s2.lower().strip()

            # Quick length check — skip obviously different sentences
            len_ratio = min(len(s1_low), len(s2_low)) / max(len(s1_low), len(s2_low), 1)
            if len_ratio < 0.5:
                continue

            sim = SequenceMatcher(None, s1_low, s2_low).ratio()

            if sim > best_sim:
                best_sim = sim
                best_match = s2
                best_j = j

        if best_match is not None and best_j >= 0:
            used_j.add(best_j)
            matches.append({
                "sent1": s1,
                "sent2": best_match,
                "similarity": best_sim,
                "line_doc1": i + 1,
                "line_doc2": best_j + 1,
            })

    return matches


# ────────────────────── SUMMARY ──────────────────────

def get_match_summary(matches, total_sents_doc1):
    """
    Return a quick summary dict for a set of sentence matches.

    Keys: ``matched_count``, ``total_sentences``, ``match_percentage``
    """
    if total_sents_doc1 == 0:
        return {"matched_count": 0, "total_sentences": 0, "match_percentage": 0.0}

    return {
        "matched_count": len(matches),
        "total_sentences": total_sents_doc1,
        "match_percentage": len(matches) / total_sents_doc1 * 100,
    }
