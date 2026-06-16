"""
reader.py — File reading and metadata extraction.

Reads PDF, DOCX, and TXT files and extracts both content
and file-system / document metadata for authorship detection.
"""

import os

from PyPDF2 import PdfReader
from docx import Document


# ────────────────────── SINGLE FILE ──────────────────────

def read_file(filepath):
    """
    Read a document and return its content + metadata.

    Supports: .txt, .pdf, .docx

    Returns
    -------
    dict  –  {"filename", "filepath", "content", "metadata"}
    None  –  if the file could not be read or is empty.
    """
    ext = os.path.splitext(filepath)[1].lower()
    filename = os.path.basename(filepath)

    # ── File-system metadata ──
    stat = os.stat(filepath)
    metadata = {
        "file_size": stat.st_size,
        "modified_time": stat.st_mtime,
        "created_time": getattr(stat, "st_birthtime", stat.st_ctime),
        "pdf_author": None,
        "pdf_creator": None,
        "pdf_creation_date": None,
    }

    content = ""

    try:
        if ext == ".txt":
            with open(filepath, encoding="utf-8", errors="ignore") as f:
                content = f.read()

        elif ext == ".pdf":
            reader = PdfReader(filepath)
            content = " ".join(
                page.extract_text() or "" for page in reader.pages
            )
            # Extract embedded PDF metadata
            info = reader.metadata
            if info:
                metadata["pdf_author"] = (
                    str(info.author) if info.author else None
                )
                metadata["pdf_creator"] = (
                    str(info.creator) if info.creator else None
                )
                metadata["pdf_creation_date"] = (
                    str(info.creation_date) if info.creation_date else None
                )

        elif ext == ".docx":
            doc = Document(filepath)
            content = "\n".join(p.text for p in doc.paragraphs)

        else:
            return None

    except Exception:
        return None

    if not content.strip():
        return None

    return {
        "filename": filename,
        "filepath": filepath,
        "content": content,
        "metadata": metadata,
    }


# ────────────────────── FOLDER SCAN ──────────────────────

SUPPORTED_EXTENSIONS = (".txt", ".pdf", ".docx")


def scan_folder(folder_path):
    """
    Recursively scan *folder_path* for supported documents.

    Returns a list of document dicts produced by ``read_file``.
    """
    documents = []

    if not os.path.isdir(folder_path):
        return documents

    for root, _dirs, filenames in os.walk(folder_path):
        for filename in sorted(filenames):
            if filename.lower().endswith(SUPPORTED_EXTENSIONS):
                filepath = os.path.join(root, filename)
                doc = read_file(filepath)
                if doc:
                    documents.append(doc)

    return documents
