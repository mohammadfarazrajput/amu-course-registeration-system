# 📜 Certificate Extractor & Classifier API

A **FastAPI backend** that accepts student certificates (PDF or Image), extracts structured information using **Google Gemini AI**, classifies them into categories, and saves everything to a **CSV file**.

---

## 🚀 Features

- ✅ Upload single or bulk certificates (PDF, JPG, PNG, WEBP)
- ✅ Extracts: Student Name, Organisation, Event Name, Event Date, Issue Date, Duration
- ✅ Classifies into fixed categories + suggests new ones via AI
- ✅ Saves all results to `extracted_certificates.csv`
- ✅ Download CSV via API endpoint
- ✅ Filter records by category
- ✅ Auto-documented API via Swagger UI

---

## 📁 Project Structure

```
certificate_extractor/
├── main.py                   # FastAPI application
├── requirements.txt          # Python dependencies
├── .env.example              # Environment variable template
├── .env                      # Your actual API key (create this)
├── extracted_certificates.csv  # Auto-generated output
└── uploads/                  # Temp upload directory
```

---

## ⚙️ Setup

### 1. Clone / copy the project folder

### 2. Create a virtual environment
```bash
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set up your Gemini API Key
```bash
cp .env.example .env
# Edit .env and paste your key:
# GEMINI_API_KEY=your_actual_key_here
```
Get your key free at: https://aistudio.google.com/app/apikey

### 5. Run the server
```bash
uvicorn main:app --reload
```

Server starts at: **http://localhost:8000**

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API info & available endpoints |
| GET | `/categories` | List all fixed classification categories |
| POST | `/extract` | Upload & process a **single** certificate |
| POST | `/extract/bulk` | Upload & process **multiple** certificates |
| GET | `/records` | View all extracted records (with optional `?category=` filter) |
| GET | `/download/csv` | Download the full CSV file |
| DELETE | `/records/clear` | Clear all records and reset CSV |

---

## 🧪 Testing via Swagger UI

Open your browser and go to:
```
http://localhost:8000/docs
```
You'll get a full interactive API documentation page where you can upload files and test everything.

---

## 📊 Extracted Fields

| Field | Description |
|-------|-------------|
| `student_name` | Recipient's full name |
| `organisation` | Issuing organisation/institution |
| `event_name` | Name of the event/course/competition |
| `event_date` | When the event took place |
| `issue_date` | When the certificate was issued |
| `duration` | Duration of the event/program |
| `category` | Classification (fixed or AI-suggested) |
| `suggested_tags` | 3–5 descriptive tags |
| `description` | Short summary of the certificate |
| `certificate_type` | participation / achievement / completion / etc. |
| `confidence_score` | How clearly Gemini could read the certificate (0–1) |

---

## 🗂️ Fixed Categories

- Hackathon
- Seminar
- Webinar
- Workshop
- Competition
- Conference
- Course / MOOC
- Internship
- Research Paper / Publication
- Sports / Cultural Event
- Volunteer / Social Work
- Training Program
- Award / Achievement
- Other *(+ AI can suggest entirely new categories)*

---

## 📦 Tech Stack

- **FastAPI** — Backend framework
- **Google Gemini 1.5 Flash** — AI extraction & classification
- **PyMuPDF** — PDF to image rendering
- **PyPDF2** — PDF text extraction fallback
- **Pillow** — Image handling
- **Pandas** — CSV management

---

## 💡 Notes

- For best results, upload clear, high-resolution certificates
- PDFs are converted to images before sending to Gemini for better accuracy
- All data is appended to `extracted_certificates.csv` — nothing is overwritten
