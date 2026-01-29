import re, collections, os
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from docx import Document
from PyPDF2 import PdfReader

# --- PDF & EMAIL ---
from fpdf import FPDF
import smtplib
from email.message import EmailMessage
import getpass


# ---------------- CLEANING ----------------
def clean_text(text):
    text = re.sub(r'\b(id|roll|reg|registration|date|sl|no)[\s:]*\d+\b', '', text, flags=re.I)
    return re.sub(r'\s+', ' ', text).strip().lower()


# ---------------- SUMMARIZATION ----------------
def summarize(text):
    sample = text[:3000]
    sents = re.split(r'(?<=[.!?]) +', sample)
    if len(sents) <= 2:
        return sample.capitalize()

    words = re.findall(r'\w+', sample.lower())
    freq = collections.Counter(words)
    scores = {
        i: sum(freq.get(w, 0) for w in re.findall(r'\w+', s.lower())) / (len(s.split()) + 1)
        for i, s in enumerate(sents[:10])
    }
    top = sorted(scores, key=scores.get, reverse=True)[:2]
    return " ".join([sents[i] for i in sorted(top)]).strip().capitalize() + "..."


# ---------------- FILE READING ----------------
def read_file(filepath):
    ext = os.path.splitext(filepath)[1].lower()

    try:
        if ext == ".txt":
            with open(filepath, encoding="utf-8") as f:
                return f.read()

        elif ext == ".pdf":
            reader = PdfReader(filepath)
            return " ".join(page.extract_text() or "" for page in reader.pages)

        elif ext == ".docx":
            doc = Document(filepath)
            return " ".join(p.text for p in doc.paragraphs)

    except Exception:
        return ""

    return ""


# ---------------- SIMILARITY ----------------
def build_similarity(cleaned_docs):
    files = list(cleaned_docs.keys())
    vectorizer = HashingVectorizer(stop_words='english', n_features=1024)
    matrix = vectorizer.transform(cleaned_docs.values())
    sim = cosine_similarity(matrix)
    return files, sim


# ---------------- GROUPING ----------------
def group_documents(files, sim_matrix, threshold=0.75):
    groups, used = [], set()

    for i in range(len(files)):
        if files[i] in used:
            continue

        group = [files[i]]
        used.add(files[i])

        for j in range(len(files)):
            if i != j and files[j] not in used and sim_matrix[i][j] >= threshold:
                group.append(files[j])
                used.add(files[j])

        groups.append(group)

    return groups


# ---------------- DISCREPANCY DETECTION ----------------
def analyze_group(group, cleaned_docs):
    if len(group) <= 1:
        return []

    data = {
        doc: {
            "years": set(re.findall(r'\b(20\d{2})\b', cleaned_docs[doc])),
            "rules": set(re.findall(r'\b(mandatory|must|optional|may|prohibited)\b', cleaned_docs[doc]))
        }
        for doc in group
    }

    issues = []

    years = set().union(*(d["years"] for d in data.values()))
    if len(years) > 1:
        issues.append(f"Timeline conflict detected: {', '.join(sorted(years))}")

    rules = set().union(*(d["rules"] for d in data.values()))
    if {"mandatory", "must"} & rules and "optional" in rules:
        issues.append("Policy contradiction: mandatory vs optional statements found")

    return issues


# ---------------- REPORT HELPERS ----------------
def similarity_label(score):
    if score >= 0.90:
        return "Fully Identical"
    elif score >= 0.75:
        return "Highly Similar"
    elif score >= 0.50:
        return "Moderately Similar"
    elif score >= 0.30:
        return "Slightly Similar"
    else:
        return "Distinct Content"


# ---------------- PROFESSIONAL REPORT ----------------
def generate_report(groups, cleaned_docs, sim_matrix, files):
    report = []

    report.append("DOCUMENT SIMILARITY ANALYSIS REPORT")
    report.append("=" * 55)
    report.append("Objective:")
    report.append(
        "To detect duplicate or previously submitted documents and ensure originality "
        "by analyzing similarity across multiple submissions.\n"
    )

    report.append("Dataset Overview:")
    report.append(f"• Total documents analyzed: {len(files)}")
    report.append("• Supported formats: TXT, PDF, DOCX")
    report.append("• Vectorization: Hashing Vectorizer")
    report.append("• Similarity Measure: Cosine Similarity")
    report.append("• Grouping Threshold: 75%\n")

    for idx, group in enumerate(groups, 1):
        report.append(f"Group {idx}")
        report.append("-" * 30)

        report.append(
            "Classification: DUPLICATE / ALREADY SUBMITTED"
            if len(group) > 1 else
            "Classification: UNIQUE / NEW SUBMISSION"
        )

        report.append("Documents:")
        for doc in group:
            report.append(f"  - {doc}")

        if len(group) > 1:
            report.append("Similarity Evaluation:")
            for i in range(len(group)):
                for j in range(i + 1, len(group)):
                    f1 = files.index(group[i])
                    f2 = files.index(group[j])
                    score = sim_matrix[f1][f2]
                    report.append(
                        f"  {group[i]} ↔ {group[j]} : {score:.2f} ({similarity_label(score)})"
                    )

        issues = analyze_group(group, cleaned_docs)
        if issues:
            report.append("Detected Inconsistencies:")
            for issue in issues:
                report.append(f"  • {issue}")

        report.append("")

    report.append("=" * 55)
    report.append("Overall Analysis Summary:")
    report.append(f"• Average similarity score: {sim_matrix.mean():.2f}")

    duplicate_groups = sum(1 for g in groups if len(g) > 1)
    report.append(f"• Duplicate document groups detected: {duplicate_groups}")
    report.append(f"• Unique document submissions: {len(groups) - duplicate_groups}\n")

    report.append("Final Conclusion:")
    report.append(
        "The system successfully identifies duplicate and highly similar documents "
        "across multiple formats, ensuring submission originality and integrity.\n"
    )

    report.append("Decision Support:")
    report.append(
        "• DUPLICATE documents should be rejected or flagged for review.\n"
        "• UNIQUE documents are eligible for further evaluation or approval."
    )

    return "\n".join(report)


# ---------------- PDF SAFETY ----------------
def make_pdf_safe(text):
    replacements = {
        "•": "-",
        "✔": "OK",
        "❌": "X",
        "↔": "<->",
        "–": "-",
        "—": "-",
        "“": '"',
        "”": '"',
        "’": "'",
        "‘": "'"
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text.encode("latin-1", "ignore").decode("latin-1")


# ---------------- TXT → PDF ----------------
def convert_txt_to_pdf(txt_path, pdf_path):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=11)

    with open(txt_path, "r", encoding="utf-8") as f:
        safe_text = make_pdf_safe(f.read())
        for line in safe_text.split("\n"):
            pdf.multi_cell(0, 6, line)

    pdf.output(pdf_path)


# ---------------- EMAIL ----------------
def send_email_with_attachment(pdf_path):
    sender =  "scriptsculptor9@gmail.com"
    receiver = input("Enter receiver email: ").strip()
    password = "rtma cpxc wdfg xfym"

    msg = EmailMessage()
    msg["Subject"] = "Document Similarity Analysis Report"
    msg["From"] = sender
    msg["To"] = receiver
    msg.set_content("Please find the attached document similarity analysis report.")

    with open(pdf_path, "rb") as f:
        msg.add_attachment(
            f.read(),
            maintype="application",
            subtype="pdf",
            filename=os.path.basename(pdf_path)
        )

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(sender, password)
        server.send_message(msg)

    print("✔ Email sent successfully.")


# ---------------- MAIN ----------------
def main():
    folder = input("Enter folder path to analyze documents: ").strip()

    if not os.path.exists(folder):
        print("❌ Folder not found.")
        return

    SUPPORTED_FILES = (".txt", ".pdf", ".docx")
    docs = {}

    for file in os.listdir(folder):
        if file.lower().endswith(SUPPORTED_FILES):
            content = read_file(os.path.join(folder, file))
            if content.strip():
                docs[file] = content

    cleaned_docs = {k: clean_text(v) for k, v in docs.items() if clean_text(v)}

    if len(cleaned_docs) < 2:
        print("❌ Not enough valid documents for comparison.")
        return

    files, sim_matrix = build_similarity(cleaned_docs)
    groups = group_documents(files, sim_matrix)

    report = generate_report(groups, cleaned_docs, sim_matrix, files)

    with open("output_report.txt", "w", encoding="utf-8") as f:
        f.write(report)

    print("✔ Document analysis completed successfully.")
    print("✔ TXT report generated: output_report.txt")

    pdf_file = "output_report.pdf"
    convert_txt_to_pdf("output_report.txt", pdf_file)
    print("✔ PDF report generated:", pdf_file)

    if input("Do you want to send the PDF report via email? (yes/no): ").lower() in ("yes", "y"):
        send_email_with_attachment(pdf_file)


if __name__ == "__main__":
    main()
