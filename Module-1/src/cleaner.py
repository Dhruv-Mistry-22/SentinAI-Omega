"""
cleaner.py — Text cleaning and metadata stripping.

Aggressively removes student-specific metadata (names, roll numbers,
dates, headers/footers) so that only the *actual assignment content*
is compared across submissions.
"""

import re
import nltk
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords


# ────────────────────── NLTK BOOTSTRAP ──────────────────────

def ensure_nltk_data():
    """Download required NLTK datasets if not already present."""
    resources = {
        "punkt_tab": "tokenizers/punkt_tab",
        "stopwords": "corpora/stopwords",
        "wordnet": "corpora/wordnet",
    }
    for name, path in resources.items():
        try:
            nltk.data.find(path)
        except LookupError:
            nltk.download(name, quiet=True)


# ────────────────────── METADATA PATTERNS ──────────────────────

_METADATA_PATTERNS = [
    # Roll / registration / ID numbers
    r'\b(?:roll|reg|registration|id|student\s*id|enrollment)'
    r'\s*(?:no|number|#)?[\s.:]*\d+\b',
    # Dates  (dd/mm/yyyy, dd-mm-yyyy, etc.)
    r'\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b',
    # Dates  (January 5, 2025)
    r'\b(?:january|february|march|april|may|june|july|august|'
    r'september|october|november|december)\s+\d{1,2},?\s*\d{2,4}\b',
    # Page numbers
    r'\bpage\s*\d+\b',
    r'\b(?:pg|p)\.\s*\d+\b',
    # Common submission headers
    r'\b(?:submitted\s+(?:by|to)|prepared\s+by|name\s*:|'
    r'student\s*name\s*:|class\s*:|section\s*:|subject\s*:|'
    r'date\s*:|assignment\s*(?:no|number|#)?\s*:?)\s*[^\n]*',
    # Serial numbers at line start
    r'^\s*(?:sl|s)\s*\.?\s*no\s*\.?\s*\d+',
]

_COMPILED_PATTERNS = [
    re.compile(p, re.IGNORECASE | re.MULTILINE) for p in _METADATA_PATTERNS
]


# ────────────────────── PUBLIC API ──────────────────────

def clean_for_comparison(text):
    """
    Aggressively clean text for similarity comparison.

    * Strips all student metadata
    * Lowercases and normalises whitespace
    * Removes punctuation / special characters
    """
    for pattern in _COMPILED_PATTERNS:
        text = pattern.sub(" ", text)

    text = re.sub(r"\s+", " ", text).strip().lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def clean_for_comparison_advanced(text):
    """
    Like ``clean_for_comparison`` but also applies lemmatisation
    and stop-word removal for the TF-IDF layer.
    """
    ensure_nltk_data()
    text = clean_for_comparison(text)

    lemmatizer = WordNetLemmatizer()
    stop_words = set(stopwords.words("english"))

    words = text.split()
    words = [
        lemmatizer.lemmatize(w)
        for w in words
        if w not in stop_words and len(w) > 2
    ]
    return " ".join(words)


def clean_for_display(text, max_length=500):
    """Lightly clean text for human-readable display in reports."""
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > max_length:
        text = text[:max_length] + "..."
    return text
