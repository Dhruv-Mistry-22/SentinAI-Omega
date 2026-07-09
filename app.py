from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import shutil
import tempfile
import os
import sys

# Import our wrappers
from api_module1 import analyze_documents
from api_module2 import classify_image

# Ensure reader is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "Module-1"))
from src.reader import read_file

app = FastAPI(title="SentienOmega Unified API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure static directory exists
os.makedirs("static", exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def serve_landing():
    """Serves the landing page."""
    with open("static/landing.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/signup", response_class=HTMLResponse)
async def serve_signup():
    """Serves the signup page."""
    with open("static/signup.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/login", response_class=HTMLResponse)
async def serve_login():
    """Serves the login page (same as signup with login tab active)."""
    with open("static/signup.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/app", response_class=HTMLResponse)
async def serve_app():
    """Serves the main application."""
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()


@app.post("/api/module1/analyze")
async def api_module1_analyze(files: list[UploadFile] = File(...)):
    """
    Accepts multiple document files, temporarily saves them, reads their content,
    and returns the plagiarism and AI detection analysis.
    """
    if len(files) < 2:
        return JSONResponse(status_code=400, content={"error": "At least 2 documents are required for analysis."})

    # Create a temporary directory to store uploaded files
    with tempfile.TemporaryDirectory() as temp_dir:
        documents = []
        for file in files:
            # Secure filename and save
            filename = file.filename
            filepath = os.path.join(temp_dir, filename)
            with open(filepath, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # Read file using Module 1's reader
            doc = read_file(filepath)
            if doc:
                # Override the file size and times if necessary, but reader.py handles it
                documents.append(doc)

        if len(documents) < 2:
             return JSONResponse(status_code=400, content={"error": "Could not extract text from at least 2 documents."})

        # Run analysis
        try:
            results = analyze_documents(documents)
            if "error" in results:
                return JSONResponse(status_code=400, content=results)
            
            from fastapi.responses import FileResponse
            if "pdf_path" in results:
                return FileResponse(
                    path=results["pdf_path"],
                    filename="SentienOmega_Report.pdf",
                    media_type="application/pdf"
                )
            
            return results
        except Exception as e:
            return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/api/module2/classify")
async def api_module2_classify(image: UploadFile = File(...), category: str = Form(None)):
    """
    Accepts an image file and an optional forced category (shoe, handbag, watch).
    Temporarily saves it and runs the classifier.
    """
    if category and category.lower() not in ["shoe", "handbag", "watch"]:
        category = None

    with tempfile.TemporaryDirectory() as temp_dir:
        filepath = os.path.join(temp_dir, image.filename)
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)

        try:
            results = classify_image(filepath, category)
            if not results.get("success"):
                return JSONResponse(status_code=400, content=results)
            return results
        except Exception as e:
            return JSONResponse(status_code=500, content={"error": str(e)})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
