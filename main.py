"""
Certificate Extractor & Classifier
===================================
FastAPI backend that accepts certificate uploads (PDF/Image),
extracts structured information using Google Gemini, classifies
into multi-label binary categories, and saves results to CSV.
"""

import os
import uuid
import csv
import json
import base64
from pathlib import Path
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai
from PIL import Image
import PyPDF2
import io
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

# ─── Config ────────────────────────────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY_HERE")
CSV_OUTPUT_PATH = Path("extracted_certificates.csv")
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash-lite")

# ─── All Multi-Label Categories ────────────────────────────────────────────────
# Each becomes an individual binary (0/1) column: cat_<name>
# Gemini sets each to 1 if the certificate belongs to that domain/type.
ALL_CATEGORIES = [
    # ── Event Format ──
    "hackathon",
    "competition",
    "seminar",
    "webinar",
    "workshop",
    "conference",
    "bootcamp",
    "symposium",
    "expo",
    "summit",

    # ── Academic / Learning ──
    "course_mooc",
    "training_program",
    "internship",
    "research",
    "publication",
    "thesis",
    "academic_excellence",

    # ── Technology ──
    "technology",
    "artificial_intelligence",
    "cybersecurity",
    "data_science",
    "web_development",
    "robotics",
    "iot",
    "cloud_computing",
    "blockchain",
    "software_engineering",
    "hardware_electronics",

    # ── Science ──
    "science",
    "mathematics",
    "physics",
    "chemistry",
    "biology",
    "environmental_science",

    # ── Business & Finance ──
    "business",
    "finance",
    "entrepreneurship",
    "marketing",
    "management",
    "economics",
    "accounting",
    "stock_market",

    # ── Arts & Design ──
    "arts",
    "design",
    "photography",
    "music",
    "dance",
    "theatre_drama",
    "film_media",
    "creative_writing",
    "architecture",

    # ── Sports & Fitness ──
    "sports",
    "fitness_yoga",
    "martial_arts",
    "esports_gaming",

    # ── Social & Humanitarian ──
    "social_work",
    "ngo_volunteering",
    "community_service",
    "disaster_relief",
    "education_outreach",

    # ── Health & Medical ──
    "healthcare",
    "first_aid",
    "mental_health",
    "nutrition",

    # ── Law & Policy ──
    "law",
    "public_policy",
    "human_rights",

    # ── Languages & Communication ──
    "language_learning",
    "public_speaking",
    "debate",
    "journalism",

    # ── Leadership & Soft Skills ──
    "leadership",
    "teamwork",
    "communication_skills",
    "personality_development",
    "project_management",

    # ── Achievement Type ──
    "winner_1st",
    "runner_up",
    "participation",
    "appreciation",
    "scholarship",
    "award_honour",
    "certification_completion",
]

# ─── CSV Headers ───────────────────────────────────────────────────────────────
BASE_HEADERS = [
    "id", "filename", "student_name", "organisation", "event_name",
    "event_date", "issue_date", "duration",
    "primary_category",
    "suggested_tags",
    "description",
    "certificate_type",
    "confidence_score",
    "processed_at",
]
CATEGORY_COLUMNS = [f"cat_{c}" for c in ALL_CATEGORIES]
CSV_HEADERS = BASE_HEADERS + CATEGORY_COLUMNS


def ensure_csv():
    if not CSV_OUTPUT_PATH.exists():
        with open(CSV_OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
            writer.writeheader()

ensure_csv()

# ─── FastAPI App ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="Certificate Extractor & Classifier",
    description="Upload student certificates, extract info with Gemini AI, multi-label classify & export ML-ready CSV.",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Pydantic Models ───────────────────────────────────────────────────────────
class CertificateData(BaseModel):
    id: str
    filename: str
    student_name: Optional[str] = None
    organisation: Optional[str] = None
    event_name: Optional[str] = None
    event_date: Optional[str] = None
    issue_date: Optional[str] = None
    duration: Optional[str] = None
    primary_category: Optional[str] = None
    suggested_tags: Optional[list[str]] = []
    description: Optional[str] = None
    certificate_type: Optional[str] = None
    confidence_score: Optional[float] = None
    processed_at: str
    category_labels: Optional[dict] = {}


class BulkResponse(BaseModel):
    total: int
    successful: int
    failed: int
    results: list


# ─── Helpers ───────────────────────────────────────────────────────────────────
def pdf_to_images(pdf_bytes: bytes) -> list:
    images = []
    try:
        import fitz
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        for page in doc:
            pix = page.get_pixmap(dpi=150)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            images.append(img)
    except ImportError:
        pass
    return images


def extract_pdf_text(pdf_bytes: bytes) -> str:
    try:
        reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text.strip()
    except Exception:
        return ""


def build_extraction_prompt() -> str:
    cat_lines = "\n".join(f'    "{c}": 0' for c in ALL_CATEGORIES)
    return f"""
You are an expert certificate analyser and multi-label classifier.
Carefully read the certificate and extract all information visible on it.

Return ONLY a single valid JSON object — no markdown, no code fences, no extra text.

{{
  "student_name": "Full name of the recipient (null if not found)",
  "organisation": "Name of issuing organisation or institution (null if not found)",
  "event_name": "Name of event, course, competition, or program (null if not found)",
  "event_date": "Date the event took place — YYYY-MM-DD or descriptive range (null if not found)",
  "issue_date": "Date certificate was issued — YYYY-MM-DD (null if not found)",
  "duration": "Duration of event/course e.g. '2 days', '6 weeks' (null if not found)",
  "primary_category": "Single best human-readable label e.g. 'Hackathon', 'Data Science Course', 'Sports Competition'",
  "suggested_tags": ["3 to 5 short descriptive tags"],
  "description": "1-2 sentence summary of what this certificate is for",
  "certificate_type": "participation / achievement / completion / appreciation / winner / runner_up / scholarship / other",
  "confidence_score": 0.95,
  "categories": {{
{cat_lines}
  }}
}}

MULTI-LABEL CLASSIFICATION RULES for the "categories" object:
- Set each key to 1 if the certificate clearly relates to that domain/type, else 0.
- A certificate SHOULD have MULTIPLE 1s — this is multi-label, not single-label.
- Examples:
    "Python for Data Science" MOOC  →  course_mooc=1, technology=1, data_science=1, software_engineering=1, certification_completion=1
    "1st place Inter-College Cricket" →  sports=1, competition=1, winner_1st=1
    "National Hackathon Certificate" →  hackathon=1, competition=1, technology=1, software_engineering=1, participation=1 (or winner_1st=1 if won)
    "Volunteer at NGO Blood Drive"   →  social_work=1, ngo_volunteering=1, community_service=1, healthcare=1, appreciation=1
    "Classical Dance Performance"   →  arts=1, dance=1, participation=1
    "Finance & Investment Workshop" →  workshop=1, finance=1, business=1, stock_market=1, certification_completion=1
- confidence_score: 0.0–1.0 — how clearly readable and unambiguous the certificate was.
- All string values must be plain text only. Set null for any base field not determinable.
"""


async def analyse_with_gemini(file_bytes: bytes, mime_type: str, filename: str) -> dict:
    prompt = build_extraction_prompt()
    try:
        if mime_type == "application/pdf":
            images = pdf_to_images(file_bytes)
            if images:
                img_bytes = io.BytesIO()
                images[0].save(img_bytes, format="PNG")
                img_bytes.seek(0)
                image_part = {"mime_type": "image/png", "data": base64.b64encode(img_bytes.read()).decode()}
                response = model.generate_content([prompt, {"inline_data": image_part}])
            else:
                text = extract_pdf_text(file_bytes)
                if not text:
                    raise ValueError("Could not extract content from PDF.")
                response = model.generate_content(f"{prompt}\n\nCertificate Text:\n{text}")
        else:
            image_part = {"mime_type": mime_type, "data": base64.b64encode(file_bytes).decode()}
            response = model.generate_content([prompt, {"inline_data": image_part}])

        raw = response.text.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()
        return json.loads(raw)

    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Gemini returned invalid JSON: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gemini API error: {str(e)}")


def build_cert(filename: str, gemini_data: dict) -> CertificateData:
    raw_cats = gemini_data.get("categories", {})
    category_labels = {f"cat_{c}": (1 if raw_cats.get(c, 0) == 1 else 0) for c in ALL_CATEGORIES}
    return CertificateData(
        id=str(uuid.uuid4())[:8],
        filename=filename,
        student_name=gemini_data.get("student_name"),
        organisation=gemini_data.get("organisation"),
        event_name=gemini_data.get("event_name"),
        event_date=gemini_data.get("event_date"),
        issue_date=gemini_data.get("issue_date"),
        duration=gemini_data.get("duration"),
        primary_category=gemini_data.get("primary_category"),
        suggested_tags=gemini_data.get("suggested_tags", []),
        description=gemini_data.get("description"),
        certificate_type=gemini_data.get("certificate_type"),
        confidence_score=gemini_data.get("confidence_score"),
        processed_at=datetime.now().isoformat(),
        category_labels=category_labels,
    )


def save_to_csv(cert: CertificateData):
    row = {
        "id": cert.id,
        "filename": cert.filename,
        "student_name": cert.student_name,
        "organisation": cert.organisation,
        "event_name": cert.event_name,
        "event_date": cert.event_date,
        "issue_date": cert.issue_date,
        "duration": cert.duration,
        "primary_category": cert.primary_category,
        "suggested_tags": ", ".join(cert.suggested_tags) if cert.suggested_tags else "",
        "description": cert.description,
        "certificate_type": cert.certificate_type,
        "confidence_score": cert.confidence_score,
        "processed_at": cert.processed_at,
    }
    row.update(cert.category_labels or {})
    with open(CSV_OUTPUT_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
        writer.writerow(row)


ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp", "image/jpg", "application/pdf"}

def get_mime_type(filename: str, content_type: str) -> str:
    ext_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp", ".pdf": "application/pdf"}
    return ext_map.get(Path(filename).suffix.lower(), content_type)


# ─── Routes ────────────────────────────────────────────────────────────────────

@app.get("/", tags=["Health"])
def root():
    return {
        "message": "Certificate Extractor & Classifier API v2",
        "version": "2.0.0",
        "total_category_columns": len(ALL_CATEGORIES),
        "endpoints": {
            "POST /extract": "Upload single certificate",
            "POST /extract/bulk": "Upload multiple certificates",
            "GET /records": "View all extracted records",
            "GET /download/csv": "Download ML-ready CSV",
            "GET /categories": "List all binary category columns",
        }
    }


@app.get("/categories", tags=["Info"])
def get_categories():
    return {
        "total": len(ALL_CATEGORIES),
        "categories": ALL_CATEGORIES,
        "csv_columns": CATEGORY_COLUMNS,
        "note": "Each is a binary 0/1 column in the CSV. Multi-label — multiple 1s per row are expected."
    }


@app.post("/extract", response_model=CertificateData, tags=["Extract"])
async def extract_single(file: UploadFile = File(...)):
    """Upload a single certificate. Extracts info + sets multi-label binary categories. Saves to CSV."""
    file_bytes = await file.read()
    mime_type = get_mime_type(file.filename, file.content_type)
    if mime_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=400, detail="Unsupported file type. Use PDF, JPG, PNG, or WEBP.")
    gemini_data = await analyse_with_gemini(file_bytes, mime_type, file.filename)
    cert = build_cert(file.filename, gemini_data)
    save_to_csv(cert)
    return cert


@app.post("/extract/bulk", response_model=BulkResponse, tags=["Extract"])
async def extract_bulk(files: list[UploadFile] = File(...)):
    """Upload multiple certificates. All processed and saved to CSV."""
    results = []
    failed = 0
    for file in files:
        try:
            file_bytes = await file.read()
            mime_type = get_mime_type(file.filename, file.content_type)
            if mime_type not in ALLOWED_MIME_TYPES:
                results.append({"filename": file.filename, "status": "failed", "error": "Unsupported file type"})
                failed += 1
                continue
            gemini_data = await analyse_with_gemini(file_bytes, mime_type, file.filename)
            cert = build_cert(file.filename, gemini_data)
            save_to_csv(cert)
            results.append({"filename": file.filename, "status": "success", "data": cert.model_dump()})
        except Exception as e:
            results.append({"filename": file.filename, "status": "failed", "error": str(e)})
            failed += 1
    return BulkResponse(total=len(files), successful=len(files) - failed, failed=failed, results=results)


@app.get("/records", tags=["Data"])
def get_records(limit: int = 200, category: Optional[str] = None):
    """View all extracted records. Filter by primary_category using ?category=Hackathon"""
    if not CSV_OUTPUT_PATH.exists():
        return {"records": [], "total": 0}
    try:
        df = pd.read_csv(CSV_OUTPUT_PATH)
        if category:
            df = df[df["primary_category"].str.lower().str.contains(category.lower(), na=False)]
        records = df.tail(limit).fillna("").to_dict(orient="records")
        return {"records": records, "total": len(df)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/download/csv", tags=["Data"])
def download_csv():
    """Download the full ML-ready CSV with all binary category columns."""
    if not CSV_OUTPUT_PATH.exists():
        raise HTTPException(status_code=404, detail="No CSV yet. Extract some certificates first.")
    return FileResponse(path=CSV_OUTPUT_PATH, media_type="text/csv", filename="extracted_certificates.csv")


@app.delete("/records/clear", tags=["Data"])
def clear_records():
    """Reset CSV — clears all records but preserves all headers."""
    with open(CSV_OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
        writer.writeheader()
    return {"message": "All records cleared. CSV reset with headers."}
