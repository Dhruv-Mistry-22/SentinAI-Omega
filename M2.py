# =========================================================
# AI vs HUMAN DOCUMENT AUTHENTICITY VERIFIER (VS CODE)
# Supports: Direct Text | TXT | PDF | DOCX | OCR PDFs
# Includes: Send report via email
# =========================================================

# ----------------------------- IMPORTS -----------------------------
import torch
import numpy as np
import re
import nltk
import pytesseract
from transformers import GPT2Tokenizer, GPT2LMHeadModel
from spellchecker import SpellChecker
from PyPDF2 import PdfReader
from docx import Document
from pdf2image import convert_from_path
from tkinter import Tk
from tkinter.filedialog import askopenfilename
import smtplib
from email.message import EmailMessage
import getpass
from fpdf import FPDF
import os
import sys

# ----------------------------- NLTK DOWNLOADS -----------------------------
nltk.download('punkt')
nltk.download('stopwords')

# ----------------------------- CONFIGURE TESSERACT PATH -----------------------------
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# ----------------------------- CONFIGURE POPPLER PATH -----------------------------
POPPLER_PATH = r"C:\poppler-25.12.0\Library\bin"  # <- adjust as per your installation

# ----------------------------- PDF FONT PATH -----------------------------
PDF_FONT_PATH = r"DejaVuSans.ttf"  # optional, fallback to Arial if missing

# =========================================================
# FILE SELECTION FUNCTION
# =========================================================
def select_file(filetypes):
    root = Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    path = askopenfilename(filetypes=filetypes)
    root.destroy()
    return path

# =========================================================
# TEXT EXTRACTION FUNCTIONS
# =========================================================
def extract_text_from_txt(path):
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()

def extract_text_from_docx(path):
    doc = Document(path)
    return "\n".join(p.text for p in doc.paragraphs)

def extract_text_from_pdf(path):
    text = ""
    try:
        reader = PdfReader(path)
        for page in reader.pages:
            if page.extract_text():
                text += page.extract_text() + "\n"
    except Exception:
        pass
    return text.strip()

def extract_text_with_ocr(path):
    print("🧠 OCR activated (scanned or image-based PDF)...")
    if not os.path.exists(POPPLER_PATH):
        print(f"❌ Poppler path not found: {POPPLER_PATH}")
        return ""
    try:
        images = convert_from_path(path, dpi=300, poppler_path=POPPLER_PATH)
    except Exception as e:
        print("❌ OCR failed. Check Poppler installation:", e)
        return ""
    text = ""
    for img in images:
        text += pytesseract.image_to_string(img)
    return text.strip()

def extract_pdf_text(path):
    text = extract_text_from_pdf(path)
    words = re.findall(r'\w+', text)
    if len(words) < 50:
        text = extract_text_with_ocr(path)
        return text, True
    return text, False

# =========================================================
# DOCUMENT AUTHENTICITY VERIFIER
# =========================================================
class DocumentAuthenticityVerifier:
    def __init__(self):
        print("🔐 Initializing Document Authenticity Verifier...")
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
        self.model = GPT2LMHeadModel.from_pretrained("gpt2").to(self.device)
        self.model.eval()
        self.spell = SpellChecker()

    def _statistical_signature(self, text):
        tokens = self.tokenizer.encode(text)
        if len(tokens) < 50:
            return 0.0, 10.0
        probs, surprises = [], []
        for i in range(0, len(tokens), 400):
            chunk = tokens[i:i+512]
            inputs = torch.tensor([chunk]).to(self.device)
            with torch.no_grad():
                outputs = self.model(inputs, labels=inputs)
            logits = outputs.logits
            p = torch.softmax(logits, dim=-1)
            shift_p = p[..., :-1, :]
            shift_l = inputs[..., 1:]
            wp = torch.gather(shift_p, 2, shift_l.unsqueeze(2)).squeeze(2)
            probs.append(torch.mean(wp).item())
            surprises.append(-torch.mean(torch.log(wp + 1e-10)).item())
        return np.mean(probs), np.mean(surprises)

    def _human_noise(self, text):
        words = re.findall(r'\w+', text.lower())
        typos = len(self.spell.unknown([w for w in words if len(w) > 3]))
        punctuation_errors = len(re.findall(r'\s[,\.!?]', text)) + len(re.findall(r'[,\.!?][A-Za-z]', text))
        case_errors = sum(1 for s in nltk.sent_tokenize(text) if s and s[0].islower())
        return (typos * 8) + (punctuation_errors * 4) + (case_errors * 10)

    def _burstiness(self, text):
        sentences = nltk.sent_tokenize(text)
        lengths = [len(s.split()) for s in sentences]
        return np.std(lengths) if len(lengths) > 1 else 0

    def verify(self, text, is_ocr=False):
        words = re.findall(r'\w+', text)
        if len(words) < 20:
            return "Unable to verify (Too little text)", "N/A"
        avg_prob, surprise = self._statistical_signature(text)
        burst = self._burstiness(text)
        noise = self._human_noise(text)
        if is_ocr:
            noise *= 0.3
        score = (
            min(100, avg_prob * 900) * 0.45 +
            min(100, (9 - surprise) * 20) * 0.35 +
            min(100, (14 - burst) * 7) * 0.20
        ) - noise
        score = min(99.8, max(0.2, score))
        if score > 80:
            verdict = "High Confidence: AI-Generated"
        elif score > 50:
            verdict = "Likely AI-Generated"
        else:
            verdict = "Likely Human-Written"
        if len(words) < 80:
            verdict += " (Low Confidence)"
        return verdict, f"{score:.1f}%"

# =========================================================
# PDF REPORT & EMAIL
# =========================================================
def make_pdf_report(text, pdf_file="document_report.pdf"):
    pdf = FPDF()
    pdf.add_page()
    try:
        if os.path.exists(PDF_FONT_PATH):
            pdf.add_font("DejaVu", "", PDF_FONT_PATH, uni=True)
            pdf.set_font("DejaVu", size=11)
        else:
            raise FileNotFoundError
    except Exception:
        print("⚠ Font file not found. Using default Arial font.")
        pdf.set_font("Arial", size=11)

    # Safely write lines to PDF
    for line in text.split("\n"):
        try:
            pdf.multi_cell(0, 6, line)
        except UnicodeEncodeError:
            safe_line = line.encode("latin-1", errors="replace").decode("latin-1")
            pdf.multi_cell(0, 6, safe_line)

    pdf.output(pdf_file)
    return pdf_file

def send_email(pdf_file):
    print("⚠ NOTE: Use a Gmail account with App Password (not regular password).")
    sender = "scriptsculptor9@gmail.com"
    password = "rtma cpxc wdfg xfym"
    recipient = input("Enter recipient email: ").strip()
    msg = EmailMessage()
    msg["Subject"] = "Document Verification Report"
    msg["From"] = sender
    msg["To"] = recipient
    msg.set_content("Please find the attached document verification report.")
    try:
        with open(pdf_file, "rb") as f:
            msg.add_attachment(f.read(), maintype="application", subtype="pdf", filename=pdf_file)
    except Exception as e:
        print("❌ Failed to attach PDF:", e)
        return
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender, password)
            server.send_message(msg)
        print("✔ Email sent successfully!")
    except Exception as e:
        print("❌ Email sending failed:", e)

# =========================================================
# MAIN PROGRAM
# =========================================================
def main():
    verifier = DocumentAuthenticityVerifier()
    print("\n🔍 SELECT INPUT TYPE")
    print("1. Direct Text")
    print("2. TXT File")
    print("3. PDF File (Auto OCR)")
    print("4. DOCX File")
    choice = input("\nEnter choice (1/2/3/4): ").strip()

    try:
        if choice == "1":
            print("\n✍️ Enter text (press Enter twice to finish):")
            lines = []
            while True:
                line = input()
                if line == "":
                    break
                lines.append(line)
            text = "\n".join(lines)
            verdict, confidence = verifier.verify(text)

        elif choice == "2":
            path = select_file([("Text files", "*.txt")])
            text = extract_text_from_txt(path)
            verdict, confidence = verifier.verify(text)

        elif choice == "3":
            path = select_file([("PDF files", "*.pdf")])
            text, is_ocr = extract_pdf_text(path)
            if not text.strip():
                print("❌ OCR failed or PDF is empty.")
                sys.exit()
            verdict, confidence = verifier.verify(text, is_ocr)

        elif choice == "4":
            path = select_file([("Word files", "*.docx")])
            text = extract_text_from_docx(path)
            verdict, confidence = verifier.verify(text)

        else:
            raise ValueError("Invalid choice")

        print("\n📏 Extracted Text Length:", len(text))
        print("\n📊 DOCUMENT VERIFICATION RESULT")
        print("--------------------------------")
        print("Verdict      :", verdict)
        print("AI Likelihood:", confidence)

        # Save report as text
        report_text = f"Document Verification Report\n\nVerdict: {verdict}\nAI Likelihood: {confidence}\n\nExtracted Text:\n{text}"
        with open("verification_report.txt", "w", encoding="utf-8") as f:
            f.write(report_text)

        # Convert to PDF
        pdf_file = make_pdf_report(report_text)
        print("✔ PDF report generated:", pdf_file)

        # Ask to send email
        send_email_option = input("📧 Send report via email? (y/n): ").lower()
        if send_email_option in ("y", "yes"):
            send_email(pdf_file)

    except Exception as e:
        print("❌ Error:", e)

if __name__ == "__main__":
    main()
