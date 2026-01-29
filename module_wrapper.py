"""
Wrapper functions for integrating M1, M2, M3 modules into Flask app.
Provides simple interfaces for document grouping, text authenticity, and image deepfake detection.
"""

import os
import sys
import json
import traceback
from typing import Tuple, Dict, Any
import tempfile
import shutil

print("[WRAPPER] Module wrapper initialized")

# ============================================
# MODULE 1: DOCUMENT GROUPING & DUPLICATE CHECK
# ============================================

def analyze_document_m1(filepaths: list) -> Tuple[str, int, str]:
    """
    Analyze multiple documents for grouping/duplicate detection.
    M1 compares documents together to find duplicates.
    
    Args:
        filepaths: List of file paths to analyze together
    
    Returns: (label, score, message)
    - label: "UNIQUE" or "DUPLICATE_GROUP" or "HAS_DUPLICATES"
    - score: 0-100 (duplicate count / total count * 100)
    - message: detailed report
    """
    try:
        print(f"[M1] Starting analysis on {len(filepaths)} document(s)")
        from M1 import read_file, clean_text, build_similarity, group_documents, generate_report
        
        # Validate inputs
        if not filepaths or len(filepaths) == 0:
            msg = "No files provided for analysis"
            print(f"[M1] {msg}")
            return "ERROR", 0, msg
        
        print(f"[M1] Reading {len(filepaths)} files...")
        
        # Read and clean all documents
        cleaned_docs = {}
        for filepath in filepaths:
            try:
                content = read_file(filepath)
                if content and len(content.strip()) > 30:
                    filename = os.path.basename(filepath)
                    cleaned_docs[filename] = clean_text(content)
                    print(f"[M1] ✓ Loaded: {filename}")
            except Exception as e:
                print(f"[M1] ⚠ Skipped {os.path.basename(filepath)}: {e}")
        
        if len(cleaned_docs) < 2:
            # Only one valid file - mark as unique
            print(f"[M1] Only 1 valid document found")
            msg = "Only 1 document analyzed - marked as UNIQUE (need 2+ docs for comparison)"
            return "UNIQUE", 100, msg
        
        print(f"[M1] Building similarity matrix for {len(cleaned_docs)} documents...")
        
        # Build similarity matrix and group
        files, sim_matrix = build_similarity(cleaned_docs)
        groups = group_documents(files, sim_matrix, threshold=0.75)
        
        print(f"[M1] Found {len(groups)} document group(s)")
        
        # Generate report
        report_text = generate_report(groups, cleaned_docs, sim_matrix, files)
        
        # Analyze groups to determine result
        duplicate_groups = [g for g in groups if len(g) > 1]
        
        if len(duplicate_groups) == 0:
            label = "ALL_UNIQUE"
            score = 100
            message = f"✓ All {len(cleaned_docs)} documents are UNIQUE. No duplicates detected."
        elif len(duplicate_groups) == 1 and len(duplicate_groups[0]) == len(cleaned_docs):
            label = "ALL_DUPLICATE"
            score = 5
            message = f"⚠ All {len(cleaned_docs)} documents are HIGHLY SIMILAR - likely duplicates!"
        else:
            dup_count = sum(len(g) - 1 for g in duplicate_groups)
            score = min(100, int((dup_count / len(cleaned_docs)) * 100))
            label = "HAS_DUPLICATES"
            message = f"Found {len(duplicate_groups)} group(s) with {dup_count} duplicate document(s). Total analyzed: {len(cleaned_docs)}"
        
        print(f"[M1] Result: {label} (score: {score})")
        print(f"[M1] Message: {message}")
        return label, score, message
    
    except Exception as e:
        msg = f"M1 Error: {str(e)}"
        print(f"[M1] {msg}")
        traceback.print_exc()
        return "ERROR", 0, msg


# ============================================
# MODULE 2: AI vs HUMAN TEXT DETECTION
# ============================================

def analyze_text_m2(filepath: str) -> Tuple[str, int, str]:
    """
    Verify if text is AI-generated or human-written using M2.
    
    Returns: (label, score, message)
    - label: "HUMAN_TEXT" or "AI_TEXT"
    - score: 0-100 confidence
    - message: verdict details
    """
    try:
        print(f"[M2] Starting analysis on {filepath}")
        from M2 import (
            DocumentAuthenticityVerifier,
            extract_text_from_txt,
            extract_text_from_docx,
            extract_pdf_text
        )
        
        # Extract text based on file type
        ext = os.path.splitext(filepath)[1].lower()
        
        if ext == '.txt':
            text = extract_text_from_txt(filepath)
        elif ext == '.pdf':
            text, _ = extract_pdf_text(filepath)
        elif ext == '.docx':
            text = extract_text_from_docx(filepath)
        else:
            msg = f"Unsupported file type: {ext}"
            print(f"[M2] {msg}")
            return "ERROR", 0, msg
        
        if not text or len(text.strip()) < 30:
            msg = "Insufficient text in file for analysis"
            print(f"[M2] {msg}")
            return "ERROR", 0, msg
        
        # Run verification
        print(f"[M2] Initializing verifier...")
        verifier = DocumentAuthenticityVerifier()
        verdict, confidence = verifier.verify(text)
        
        # Parse confidence
        try:
            score = int(float(confidence.replace('%', '')))
        except:
            score = 50
        
        label = "AI_TEXT" if score > 50 else "HUMAN_TEXT"
        
        print(f"[M2] Verdict: {verdict}, Score: {score}%")
        return label, score, verdict
    
    except Exception as e:
        msg = f"M2 Error: {str(e)}"
        print(f"[M2] {msg}")
        traceback.print_exc()
        return "ERROR", 0, msg


# ============================================
# MODULE 3: DEEPFAKE / AI IMAGE DETECTION
# ============================================

def analyze_image_m3(filepath: str) -> Tuple[str, int, str]:
    """
    Detect if an image is AI-generated or a real photograph using M3.
    
    Returns: (label, score, message)
    - label: "REAL" or "AI_GENERATED"
    - score: 0-100 confidence
    - message: detailed analysis
    """
    try:
        print(f"[M3] Starting analysis on {filepath}")
        from M3 import SentinAIDetector
        
        # Check if image exists
        if not os.path.exists(filepath):
            msg = "Image file not found"
            print(f"[M3] {msg}")
            return "ERROR", 0, msg
        
        # Initialize detector
        print(f"[M3] Initializing SentinAI detector...")
        detector = SentinAIDetector()
        
        # Analyze image
        print(f"[M3] Running analysis...")
        result = detector.analyze(filepath)
        
        label = result['category']
        score = int(result['confidence_percent'])
        message = f"Analysis complete: {label} with {score}% confidence"
        
        print(f"[M3] Result: {label} (confidence: {score}%)")
        return label, score, message
    
    except Exception as e:
        msg = f"M3 Error: {str(e)}"
        print(f"[M3] {msg}")
        traceback.print_exc()
        return "ERROR", 0, msg


# ============================================
# EMAIL FUNCTIONALITY
# ============================================

def send_report_email(recipient_email: str, subject: str, body: str, report_file: str = None) -> bool:
    """
    Send analysis report to user's email.
    
    Args:
        recipient_email: User's email
        subject: Email subject
        body: Email body text
        report_file: Optional PDF attachment path
    
    Returns:
        True if sent successfully, False otherwise
    """
    try:
        print(f"[EMAIL] Preparing email to {recipient_email}")
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        from email.mime.base import MIMEBase
        from email import encoders
        
        # Gmail credentials (app-specific password)
        sender_email = "scriptsculptor9@gmail.com"
        sender_password = "rtma cpxc wdfg xfym"  # App-specific password
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        
        # If no report_file provided, generate a simple PDF from the body so
        # emails always include a PDF attachment (PDF-only reports).
        temp_pdf = None
        if not report_file:
            try:
                from fpdf import FPDF
                import tempfile
                pdf = FPDF()
                pdf.add_page()
                pdf.set_auto_page_break(auto=True, margin=15)
                pdf.set_font("Arial", size=12)
                for line in body.splitlines():
                    pdf.multi_cell(0, 8, line)

                tf = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
                temp_pdf = tf.name
                tf.close()
                pdf.output(temp_pdf)
                report_file = temp_pdf
                print(f"[EMAIL] Generated temporary PDF report: {report_file}")
            except Exception as e:
                print(f"[EMAIL] Warning: PDF generation failed: {e}")

        # Attach report if provided (either original or generated)
        if report_file and os.path.exists(report_file):
            try:
                with open(report_file, 'rb') as attachment:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f'attachment; filename= {os.path.basename(report_file)}')
                msg.attach(part)
                print(f"[EMAIL] Attached file: {report_file}")
            except Exception as e:
                print(f"[EMAIL] Warning: Could not attach file: {e}")
        
        # Send email
        print(f"[EMAIL] Connecting to Gmail SMTP...")
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        
        print(f"[EMAIL] Successfully sent to {recipient_email}")
        # Cleanup temporary PDF if we created one
        try:
            if temp_pdf and os.path.exists(temp_pdf):
                os.remove(temp_pdf)
                print(f"[EMAIL] Removed temporary PDF: {temp_pdf}")
        except Exception:
            pass
        return True
    
    except Exception as e:
        print(f"[EMAIL] Error: {str(e)}")
        traceback.print_exc()
        return False


# ============================================
# ROUTER: Dispatch to correct module
# ============================================

def analyze_file(filepath: str, module: str) -> Tuple[str, int, str]:
    """
    Route file to the appropriate analysis module.
    
    Args:
        filepath: Path to uploaded file
        module: 'duplicate' (M1), 'text' (M2), or 'image' (M3)
    
    Returns:
        (result_label, confidence_score, detailed_message)
    """
    
    if not os.path.exists(filepath):
        return "ERROR", 0, "File not found"
    
    print(f"[ROUTER] Analyzing {filepath} with module={module}")
    
    if module == 'duplicate':
        return analyze_document_m1(filepath)
    elif module == 'text':
        return analyze_text_m2(filepath)
    elif module == 'image':
        return analyze_image_m3(filepath)
    else:
        return "ERROR", 0, f"Unknown module: {module}"
