# =========================================================
# SENTINAI v2 – Hybrid AI & Forensic Image Detector + Email
# =========================================================

import os, glob, json, cv2, smtplib
import torch
import numpy as np
from PIL import Image, ExifTags
from transformers import pipeline, CLIPProcessor, CLIPModel
from scipy.stats import entropy
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

# ============================================
# SEMANTIC + FORENSIC AI DETECTOR
# ============================================

class SentinAIDetector:

    def __init__(self):
        print("🧠 Initializing SentinAI v2...")

        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        # Weak AI detector (texture-based)
        self.ai_model = pipeline(
            "image-classification",
            model="umm-maybe/AI-image-detector",
            device=0 if self.device == "cuda" else -1
        )

        # 🔥 CLIP semantic brain
        self.clip_model = CLIPModel.from_pretrained(
            "openai/clip-vit-base-patch32"
        ).to(self.device)

        self.clip_processor = CLIPProcessor.from_pretrained(
            "openai/clip-vit-base-patch32"
        )

        self.semantic_labels = [
            "a real photograph taken by a camera",
            "an AI-generated image",
            "a digital illustration",
            "a fantasy or science fiction scene",
            "a CGI render"
        ]

    # ---------- SEMANTIC REALITY CHECK ----------
    def semantic_ai_score(self, image_path):
        image = Image.open(image_path).convert("RGB")

        inputs = self.clip_processor(
            text=self.semantic_labels,
            images=image,
            return_tensors="pt",
            padding=True
        ).to(self.device)

        with torch.no_grad():
            outputs = self.clip_model(**inputs)

        probs = outputs.logits_per_image.softmax(dim=1)[0].cpu().numpy()

        score = (
            probs[1] * 1.0 +   # AI-generated
            probs[2] * 0.8 +   # illustration
            probs[3] * 0.9 +   # fantasy
            probs[4] * 0.85    # CGI
        )

        return float(score)

    # ---------- LOCAL AI MODEL ----------
    def local_ai_score(self, image_path):
        try:
            res = self.ai_model(image_path)
            for r in res:
                if "ai" in r["label"].lower():
                    return float(r["score"])
        except:
            pass
        return 0.05

    # ---------- FORENSICS ----------
    def forensic_score(self, image_path):
        img = cv2.imread(image_path)
        if img is None:
            return 0.0

        img = cv2.resize(img, (512, 512))
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        ent = entropy(np.histogram(gray, 256)[0] + 1)
        fft = np.std(np.log(np.abs(np.fft.fftshift(np.fft.fft2(gray))) + 1))

        score = 0.0
        if ent < 4.3:
            score += 0.5
        if fft < 0.85:
            score += 0.5

        return score * 0.2

    # ---------- EXIF ----------
    def has_real_exif(self, path):
        try:
            img = Image.open(path)
            exif = img._getexif()
            if not exif:
                return False
            tags = {ExifTags.TAGS.get(k): v for k, v in exif.items()}
            return "Make" in tags and "Model" in tags
        except:
            return False

    # ---------- FINAL DECISION ----------
    def analyze(self, image_path):
        semantic = self.semantic_ai_score(image_path)
        local = self.local_ai_score(image_path)
        forensic = self.forensic_score(image_path)
        exif = self.has_real_exif(image_path)

        ai_score = (
            semantic * 0.45 +
            local * 0.30 +
            forensic * 0.15
        )

        if exif:
            ai_score -= 0.10

        ai_score = min(max(ai_score, 0.01), 0.99)
        percent = round(ai_score * 100, 1)

        category = "AI_GENERATED" if percent >= 60 else "CAMERA"

        return {
            "filename": os.path.basename(image_path),
            "category": category,
            "confidence_percent": percent
        }

# ============================================
# EMAIL FUNCTION
# ============================================
def send_email(sender_email, sender_password, receiver_email, subject, body, attachment_path):
    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = receiver_email
    msg["Subject"] = subject

    msg.attach(MIMEText(body, "plain"))

    with open(attachment_path, "rb") as f:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition",
            f"attachment; filename= {os.path.basename(attachment_path)}"
        )
        msg.attach(part)

    # SMTP example using Gmail
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        print(f"✅ Email sent to {receiver_email}")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")

# ============================================
# RUNNER
# ============================================
def main():
    folder = input("📁 Enter folder path containing images: ").strip()

    images = []
    for ext in ("*.jpg", "*.jpeg", "*.png"):
        images.extend(glob.glob(os.path.join(folder, ext)))

    if not images:
        print("❌ No images found")
        return

    detector = SentinAIDetector()
    results = []

    print("\n🔍 Analyzing images...\n")
    for img in images:
        res = detector.analyze(img)
        print(json.dumps(res, indent=2))
        results.append(res)

    # Save report
    report_path = "deepfake_report.json"
    with open(report_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n✅ Report saved as {report_path}")

    # Ask user to send email
    send_choice = input("\n📧 Send report via email? (y/n): ").strip().lower()
    if send_choice == "y":
        sender = "scriptsculptor9@gmail.com"
        password = "rtma cpxc wdfg xfym"
        receiver = input("Enter recipient email: ").strip()
        subject = "SentinAI Deepfake Image Report"
        body = "Attached is the deepfake analysis report generated by SentinAI v2."
        send_email(sender, password, receiver, subject, body, report_path)

# ============================================
if __name__ == "__main__":
    main()
