🛡️ SentinAI Omega
AI & Deepfake Image Forensics + Document Trust System

SentinAI Omega is a cloud-ready AI forensics platform designed to verify the authenticity of images and documents.
It combines semantic AI analysis, image forensics, and document similarity detection to identify AI-generated, manipulated, or duplicate content.

This project was built for AutonomousHacks / GDG Hackathon, focusing on autonomous decision-making, system design, and real-world applicability.

🚀 Key Features
🔍 Image Authenticity & Deepfake Detection

Detects AI-generated vs camera-captured images

Hybrid approach:

Semantic understanding (CLIP)

Texture-based AI detection

Image forensics (entropy & frequency analysis)

Outputs confidence score and category

📄 Document Trust & Classification System

Groups documents into:

Fully same

Partially same (with discrepancies)

Completely different

Detects:

Duplicate submissions

Content inconsistencies

Supports:

TXT

PDF (Auto OCR)

DOCX

✍️ AI vs Human Text Detection

Identifies whether content is AI-written or human-written

Uses statistical language modeling and linguistic noise analysis

Handles OCR-generated text intelligently

🛡️ Admin Authentication

Secure admin-only dashboard

Session-based authentication

Protects sensitive system operations

☁️ Cloud-Ready Architecture

Web-based interface (browser accessible)

Backend deployable on cloud platforms (Render / GCP)

Scalable and modular design

🧠 System Architecture (High Level)
Frontend (Web UI)
     |
Backend (Flask / Python)
     |
AI Engines
 ├── Image Forensics
 ├── Semantic AI Detection
 ├── Document Similarity Engine
 └── Text Authenticity Analyzer
     |
Cloud Deployment (Render / GCP)

🧪 Technology Stack
Backend

Python

Flask

Torch

Transformers

AI / ML

CLIP (Semantic Image Understanding)

GPT-2 (Text Authenticity)

Scikit-learn (TF-IDF & similarity)

OpenCV (Image Forensics)

Document Processing

PyPDF2

python-docx

pytesseract

pdf2image

NLTK

Cloud & Deployment

Render (recommended)

Google Cloud compatible

📦 Requirements

Install all dependencies using:

pip install -r requirements.txt

requirements.txt
torch
transformers
numpy
opencv-python
scikit-learn
nltk
pytesseract
pdf2image
python-docx
PyPDF2
spellchecker
fpdf
Pillow
Flask

▶️ How to Run Locally
python app.py


Then open in browser:

http://127.0.0.1:5000

🔐 Admin Login

Username: admin

Password: sentinai123

(Admin credentials can be changed in app.py)

🌐 Cloud Deployment (Render)

Push project to public GitHub repository

Create a new Web Service on Render

Set:

Build Command: pip install -r requirements.txt

Start Command: python app.py

App becomes accessible via public URL

✅ This confirms cloud-based system implementation

⚠️ Limitations

AI detection is probabilistic, not absolute

Performance depends on input quality

Some AI-generated images may bypass detection (research limitation)

🔮 Future Enhancements

Database-backed user management

Admin analytics dashboard

API-based verification service

Improved multimodal deepfake detection

Blockchain-based document signatures

👨‍💻 Team – Full Stack Squad

Chaitanya – Team Leader | Backend & Frontend

Vidhi – Frontend

Harsh – Cloud & Deployment

Dhruv Mistry – AI Systems & Integration