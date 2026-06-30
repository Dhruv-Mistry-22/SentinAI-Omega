"""
api_module1.py — Web wrapper for Module 1 (Document Plagiarism & AI Detection).
"""
import os
import sys
import time

# Add Module-1 to sys.path to allow importing from its src
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "Module-1"))

from src.cleaner import clean_for_comparison, ensure_nltk_data
from src.analyzer import SimilarityAnalyzer
from src.sentence_matcher import find_matching_sentences
from src.classifier import classify_all_pairs, get_document_verdicts
from src.ai_detector import analyze_ai_characteristics

def analyze_documents(documents):
    """
    Accepts a list of dicts: [{"filename": str, "content": str, "metadata": dict}]
    Returns a dict with analysis results.
    """
    if len(documents) < 2:
        return {"error": "Need at least 2 valid documents."}

    # Preprocess
    ensure_nltk_data()
    
    files = [d["filename"] for d in documents]
    raw_texts = {}
    cleaned_texts = {}
    
    for doc in documents:
        raw_texts[doc["filename"]] = doc["content"]
        cleaned_texts[doc["filename"]] = clean_for_comparison(doc["content"])
        
    empty = [f for f in files if not cleaned_texts[f].strip()]
    if empty:
        for f in empty:
            files.remove(f)
            del cleaned_texts[f]
            del raw_texts[f]
            documents = [d for d in documents if d["filename"] != f]
            
    if len(files) < 2:
        return {"error": "Not enough valid documents after cleaning (files might be empty or unreadable)."}

    # Similarity Analysis
    analyzer = SimilarityAnalyzer()
    analysis = analyzer.analyze(files, cleaned_texts, raw_texts)
    
    # Classification
    flagged_pairs = classify_all_pairs(analysis, documents)
    verdicts = get_document_verdicts(files, flagged_pairs)
    
    # Evidence Collection
    sentence_evidence = []
    sentence_evidence_dict = {}
    if flagged_pairs:
        for pair in flagged_pairs:
            matches = find_matching_sentences(
                raw_texts[pair["file1"]],
                raw_texts[pair["file2"]],
            )
            # Store in a JSON serializable way if needed, but also populate dict for PDF
            sentence_evidence.append({
                "file1": pair["file1"],
                "file2": pair["file2"],
                "matches": matches
            })
            sentence_evidence_dict[(pair["file1"], pair["file2"])] = matches
            
    # AI Characteristics
    ai_results = analyze_ai_characteristics(raw_texts)
    
    # Generate PDF Report
    import tempfile
    from src.report_generator import generate_pdf_report
    pdf_path = os.path.join(tempfile.gettempdir(), f"SentienOmega_Report_{int(time.time())}.pdf")
    generate_pdf_report(analysis, flagged_pairs, verdicts, sentence_evidence_dict, pdf_path, ai_results)
    
    return {
        "success": True,
        "pdf_path": pdf_path,
        "files_analyzed": len(files),
        "verdicts": verdicts,
        "flagged_pairs": flagged_pairs,
        "sentence_evidence": sentence_evidence,
        "ai_results": ai_results
    }
