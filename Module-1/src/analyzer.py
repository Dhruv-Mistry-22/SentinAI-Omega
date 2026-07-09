"""
analyzer.py — Multi-layer similarity analysis engine.

Combines four complementary layers for accurate plagiarism detection:

  Layer 1  TF-IDF + Cosine Similarity   (word importance)
  Layer 2  N-gram Jaccard Similarity     (phrase-level matching)
  Layer 3  Structural Fingerprinting     (document layout)
  Layer 4  Writing-Style Analysis        (authorship fingerprint)

Scalability
-----------
For 500 + documents the engine uses a **two-phase approach**:

  Phase 1 — Fast TF-IDF screening of ALL pairs  (matrix multiplication)
  Phase 2 — Expensive Jaccard / Structure / Style only for pairs whose
            TF-IDF score exceeds ``SCREENING_THRESHOLD``

This reduces the work from O(n²) for every layer to O(n²) for TF-IDF
plus O(k) for the other layers, where k ≪ n² is the number of
"promising" pairs.
"""

import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from src.style_analyzer import compute_style_vector, compare_styles
from src.utils import progress_bar, print_info


# ────────────────────── PRIVATE HELPERS ──────────────────────

def _compute_ngram_shingles(text, n=3):
    """Return the set of word-level n-gram tuples from *text*."""
    words = text.split()
    if len(words) < n:
        return set([tuple(words)]) if words else set()
    return {tuple(words[i : i + n]) for i in range(len(words) - n + 1)}


def _jaccard_similarity(set1, set2):
    """Jaccard coefficient between two sets."""
    if not set1 and not set2:
        return 1.0
    if not set1 or not set2:
        return 0.0
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    return intersection / union if union > 0 else 0.0


def _structural_features(text):
    """Extract lightweight structural features from raw text."""
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    sentences = [s for s in sentences if len(s.split()) >= 3]
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    words = text.split()

    sent_count = max(len(sentences), 1)
    para_count = max(len(paragraphs), 1)
    word_count = max(len(words), 1)

    sent_lengths = [len(s.split()) for s in sentences] if sentences else [0]

    return {
        "sentence_count": sent_count,
        "paragraph_count": para_count,
        "word_count": word_count,
        "avg_sentence_length": sum(sent_lengths) / len(sent_lengths),
        "words_per_paragraph": word_count / para_count,
    }


def _structural_similarity(feat1, feat2):
    """Compare two structural-feature dicts → similarity in [0, 1]."""
    sims = []
    for key in feat1:
        v1, v2 = feat1[key], feat2[key]
        mx = max(v1, v2, 1)
        sims.append(min(v1, v2) / mx)
    return sum(sims) / len(sims) if sims else 0.0


# ────────────────────── PUBLIC ENGINE ──────────────────────

class SimilarityAnalyzer:
    """
    Four-layer similarity engine with fast TF-IDF screening.

    Usage::

        analyzer = SimilarityAnalyzer()
        result   = analyzer.analyze(files, cleaned_texts, raw_texts)

    ``result`` is a dict with keys:
        files, tfidf_matrix, jaccard_matrix,
        structural_matrix, style_matrix, combined_matrix
    """

    # Layer weights (must sum to 1.0)
    WEIGHTS = {
        "tfidf": 0.40,
        "jaccard": 0.30,
        "structural": 0.15,
        "style": 0.15,
    }

    # Min TF-IDF cosine to trigger the expensive layers
    SCREENING_THRESHOLD = 0.25

    def __init__(self):
        self.files = []
        self.n_docs = 0

    # ── Main entry point ──────────────────────────────────

    def analyze(self, files, cleaned_texts, raw_texts):
        """
        Run all four layers and return per-layer + combined matrices.

        Parameters
        ----------
        files : list[str]
            Ordered list of filenames.
        cleaned_texts : dict[str, str]
            {filename: aggressively-cleaned text}
        raw_texts : dict[str, str]
            {filename: raw text} (for structural / style layers)
        """
        self.files = files
        self.n_docs = n = len(files)

        total_pairs = n * (n - 1) // 2
        print_info(f"Analyzing {n} documents ({total_pairs:,} pairs) ...")

        # ── Layer 1: TF-IDF + Cosine  (ALL pairs — fast) ────
        print_info("Layer 1/4: TF-IDF + Cosine Similarity ...")
        tfidf_matrix = self._compute_tfidf(cleaned_texts)

        # ── Identify promising pairs ────────────────────────
        promising = set()
        for i in range(n):
            for j in range(i + 1, n):
                if tfidf_matrix[i][j] >= self.SCREENING_THRESHOLD:
                    promising.add((i, j))

        print_info(
            f"  {len(promising):,} promising pairs pass screening "
            f"(threshold {self.SCREENING_THRESHOLD:.0%})"
        )

        # ── Layer 2: N-gram Jaccard  (promising only) ───────
        print_info("Layer 2/4: N-gram Jaccard Similarity ...")
        jaccard_matrix = self._compute_jaccard(cleaned_texts, promising)

        # ── Layer 3: Structural  (promising only) ───────────
        print_info("Layer 3/4: Structural Fingerprinting ...")
        structural_matrix = self._compute_structural(raw_texts, promising)

        # ── Layer 4: Writing Style  (promising only) ────────
        print_info("Layer 4/4: Writing Style Analysis ...")
        style_matrix = self._compute_style(raw_texts, promising)

        # ── Combined weighted score ─────────────────────────
        combined_matrix = (
            self.WEIGHTS["tfidf"] * tfidf_matrix
            + self.WEIGHTS["jaccard"] * jaccard_matrix
            + self.WEIGHTS["structural"] * structural_matrix
            + self.WEIGHTS["style"] * style_matrix
        )

        return {
            "files": files,
            "tfidf_matrix": tfidf_matrix,
            "jaccard_matrix": jaccard_matrix,
            "structural_matrix": structural_matrix,
            "style_matrix": style_matrix,
            "combined_matrix": combined_matrix,
        }

    # ── Layer implementations ─────────────────────────────

    def _compute_tfidf(self, cleaned_texts):
        texts = [cleaned_texts[f] for f in self.files]

        vectorizer = TfidfVectorizer(
            stop_words="english",
            max_features=5000,
            ngram_range=(1, 2),      # unigrams + bigrams
            sublinear_tf=True,
        )
        tfidf_mat = vectorizer.fit_transform(texts)
        sim = cosine_similarity(tfidf_mat)
        np.fill_diagonal(sim, 0)
        return sim

    def _compute_jaccard(self, cleaned_texts, promising):
        n = self.n_docs
        matrix = np.zeros((n, n))

        # Pre-compute shingles only for docs that appear in promising pairs
        needed = {idx for pair in promising for idx in pair}
        shingles = {
            idx: _compute_ngram_shingles(cleaned_texts[self.files[idx]])
            for idx in needed
        }

        total = len(promising)
        for count, (i, j) in enumerate(promising):
            if total > 50 and count % max(1, total // 20) == 0:
                progress_bar(count, total, "  Jaccard")
            sim = _jaccard_similarity(shingles[i], shingles[j])
            matrix[i][j] = sim
            matrix[j][i] = sim

        if total > 50:
            progress_bar(total, total, "  Jaccard")

        return matrix

    def _compute_structural(self, raw_texts, promising):
        n = self.n_docs
        matrix = np.zeros((n, n))

        needed = {idx for pair in promising for idx in pair}
        feats = {
            idx: _structural_features(raw_texts[self.files[idx]])
            for idx in needed
        }

        for i, j in promising:
            sim = _structural_similarity(feats[i], feats[j])
            matrix[i][j] = sim
            matrix[j][i] = sim

        return matrix

    def _compute_style(self, raw_texts, promising):
        n = self.n_docs
        matrix = np.zeros((n, n))

        needed = {idx for pair in promising for idx in pair}
        styles = {
            idx: compute_style_vector(raw_texts[self.files[idx]])
            for idx in needed
        }

        for i, j in promising:
            sim = compare_styles(styles[i], styles[j])
            matrix[i][j] = sim
            matrix[j][i] = sim

        return matrix
