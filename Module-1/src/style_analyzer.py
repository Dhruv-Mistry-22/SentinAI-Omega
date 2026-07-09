"""
style_analyzer.py — Writing-style fingerprinting.

Every author has measurable writing habits: vocabulary richness,
sentence length, punctuation density, etc.  This module computes
a numeric "style vector" for each document and compares them.

Two copied documents will share very similar style vectors even
when a student tries to rename variables or swap a few words.
"""

import re
import math


# ────────────────────── STYLE VECTOR ──────────────────────

def compute_style_vector(text):
    """
    Compute a writing-style fingerprint for *text*.

    Returns a dict of numeric metrics that characterise the
    author's writing patterns.
    """
    # ── Split into sentences ──
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    sentences = [s for s in sentences if len(s.split()) >= 3]

    # ── Split into paragraphs ──
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    if not paragraphs:
        paragraphs = [p.strip() for p in text.split("\n") if p.strip()]

    # ── Words ──
    words = re.findall(r"\b\w+\b", text.lower())

    if not words or not sentences:
        return _empty_vector()

    total_words = len(words)
    unique_words = len(set(words))
    total_sentences = len(sentences)
    total_paragraphs = max(len(paragraphs), 1)

    # Sentence-length statistics
    sent_lengths = [len(s.split()) for s in sentences]
    avg_sent_len = sum(sent_lengths) / len(sent_lengths)
    variance = sum((l - avg_sent_len) ** 2 for l in sent_lengths) / len(sent_lengths)

    # Word-length statistics
    word_lengths = [len(w) for w in words]
    avg_word_len = sum(word_lengths) / len(word_lengths)

    # Punctuation counts
    comma_count = text.count(",")
    semicolon_count = text.count(";")
    colon_count = text.count(":")
    question_count = text.count("?")
    exclamation_count = text.count("!")

    return {
        "vocabulary_richness": unique_words / total_words,
        "avg_sentence_length": avg_sent_len,
        "sentence_length_std": math.sqrt(variance),
        "avg_word_length": avg_word_len,
        "words_per_paragraph": total_words / total_paragraphs,
        "sentences_per_paragraph": total_sentences / total_paragraphs,
        "comma_density": comma_count / total_sentences,
        "semicolon_density": semicolon_count / total_sentences,
        "colon_density": colon_count / total_sentences,
        "question_ratio": question_count / total_sentences,
        "exclamation_ratio": exclamation_count / total_sentences,
        "paragraph_count": total_paragraphs,
    }


# ────────────────────── COMPARISON ──────────────────────

def compare_styles(style1, style2):
    """
    Compare two style vectors and return a similarity in [0, 1].

    Uses per-metric exponential-decay similarity and averages across
    all metrics.  This naturally handles different scales without
    requiring explicit normalisation.
    """
    keys = [k for k in style1 if k != "paragraph_count"]

    if not keys:
        return 0.0

    similarities = []
    for key in keys:
        v1 = style1[key]
        v2 = style2[key]
        max_val = max(abs(v1), abs(v2), 0.001)
        diff = abs(v1 - v2) / max_val
        similarities.append(math.exp(-diff))

    # Paragraph-count similarity (structural)
    p1 = style1["paragraph_count"]
    p2 = style2["paragraph_count"]
    para_sim = min(p1, p2) / max(p1, p2) if max(p1, p2) > 0 else 1.0
    similarities.append(para_sim)

    return sum(similarities) / len(similarities)


# ────────────────────── HELPERS ──────────────────────

def _empty_vector():
    """Return a zeroed-out style vector for degenerate documents."""
    return {
        "vocabulary_richness": 0,
        "avg_sentence_length": 0,
        "sentence_length_std": 0,
        "avg_word_length": 0,
        "words_per_paragraph": 0,
        "sentences_per_paragraph": 0,
        "comma_density": 0,
        "semicolon_density": 0,
        "colon_density": 0,
        "question_ratio": 0,
        "exclamation_ratio": 0,
        "paragraph_count": 0,
    }
