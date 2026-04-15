# 🎓 AMU Course Registration System
**AI-Powered Academic Registration System for Zakir Husain College of Engineering & Technology**

---

## 📋 Overview

A **production-grade hybrid AI system** combining:
- **SQL Database** for structured academic data (students, courses, grades)
- **Vector Database** for semantic ordinance retrieval (RAG)
- **LangChain Agents** for intelligent reasoning
- **FastAPI Backend** for robust API layer
- **Streamlit Frontend** for user interface

**This is NOT a chatbot.** It's a structured academic registration system with AI assistance for complex rule reasoning.

---

## 🏗️ Three-Layer Architecture

```
┌───────────────────────────────────────┐
│       LAYER 1: SQL Database           │
│  Students | Courses | Registrations   │
│  Grades | CGPA | Eligibility          │
│  ✓ ACID Transactions                  │
│  ✓ Source of Truth                    │
└───────────────────────────────────────┘

┌───────────────────────────────────────┐
│    LAYER 2: Vector Database (FAISS)   │
│  Ordinances | Curriculum Policies     │
│  Amendments | Regulations             │
│  ✓ Semantic Search (RAG)              │
│  ✓ Knowledge Retrieval                │
└───────────────────────────────────────┘

┌───────────────────────────────────────┐
│     LAYER 3: Document Storage         │
│  Raw PDFs | Student Uploads           │
│  ✓ Archival                           │
│  ✓ Processing Pipeline                │
└───────────────────────────────────────┘
```

---

## ✨ Key Features

✅ Student verification with faculty/enrollment number
✅ Eligibility analysis (AMU ordinance-compliant)
✅ Course recommendations (Current + Backlogs + Advancement)
✅ Marksheet upload with OCR extraction
✅ RAG-powered chat for rule queries
✅ Multi-mode registration (A/B/C)
✅ Risk detection (name removal warnings)

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Tesseract OCR
- OpenAI or Anthropic API key

### Installation

```bash
# 1. Clone and setup
git clone <repo>
cd amu-registration-system
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Install dependencies
cd backend && pip install -r requirements.txt
cd ../frontend && pip install -r requirements.txt

# 3. Configure environment
cd ..
cp .env.example .env
# Edit .env with your API keys

# 4. Initialize system
cd scripts
python seed_database.py      # Populate SQL database
python build_vector_index.py # Build vector store
```

### Run Application

**Terminal 1 - Backend:**
```bash
cd backend
python main.py
```
→ http://localhost:8000

**Terminal 2 - Frontend:**
```bash
cd frontend
streamlit run app.py
```
→ http://localhost:8501

---

## 📁 Project Structure

```
<<<<<<< HEAD
amu-registration-system/
│
├── backend/
│   ├── agents/                  # LangChain agents
│   │   ├── graph.py            # Main orchestrator
│   │   ├── verification_agent.py
│   │   ├── eligibility_agent.py
│   │   ├── course_selector.py
│   │   └── registration_agent.py
│   │
│   ├── services/                # Core services
│   │   ├── vector_store.py     # FAISS operations
│   │   ├── retriever.py        # RAG retrieval
│   │   ├── document_processor.py
│   │   └── ocr_service.py
│   │
│   ├── models.py               # SQLAlchemy models
│   ├── business_rules.py       # AMU rules logic
│   ├── database.py             # DB connection
│   ├── schemas.py              # Pydantic schemas
│   └── main.py                 # FastAPI app
│
├── frontend/
│   ├── app.py
│   └── pages/
│       ├── dashboard.py
│       ├── courses.py
│       ├── registration.py
│       └── chat.py
│
├── data/
│   ├── raw/ordinances/        # AMU PDFs
│   ├── processed/             # Parsed data
│   ├── vector_store/          # FAISS index
│   ├── uploads/               # Student uploads
│   └── database.db            # SQLite DB
│
└── scripts/
    ├── parse_curriculum.py
    ├── seed_database.py
    └── build_vector_index.py
=======
certificate_extractor/
├── main.py                   # FastAPI application
├── requirements.txt          # Python dependencies
├── .env.example              # Environment variable template
├── .env                      # Your actual API key (create this)
├── extracted_certificates.csv  # Auto-generated output
└── uploads/                  # Temp upload directory
>>>>>>> 5be736953f63faf8fc0ead525c8dc008ff389a44
```

---

<<<<<<< HEAD
## 🎓 AMU Business Rules

### Promotion (Clause 11.1)
- Sem 2: Min 16 credits
- Sem 4: Min 60 credits (36 from Sem 1-2)
- Sem 6: Min 108 credits (80 from Sem 1-4)

### Name Removal
"Not Promoted" ≥ 3 times → Removed from rolls

### Advancement (Clause 7.2 j)
- Must be Sem 5/6
- CGPA ≥ 7.5
- No backlogs
- Prerequisites met

### Registration Modes
- **Mode A:** Full attendance + all evaluations
- **Mode B:** Evaluations only (if attendance done)
- **Mode C:** End-sem only (sessional marks reused)

---

## 🔧 Tech Stack

| Component | Technology |
|-----------|-----------|
| Frontend | Streamlit |
| Backend | FastAPI |
| Orchestration | LangChain |
| SQL DB | SQLAlchemy + SQLite |
| Vector DB | FAISS |
| LLM | GPT-4 / Claude 3.5 |
| OCR | Pytesseract |

---

## 📊 Data Flows

### Registration Flow
```
Login → Fetch Data (SQL) → Check Eligibility (RAG) 
→ Recommend Courses (SQL) → Validate → Register (SQL)
```

### Marksheet Upload
```
Upload → OCR → Parse Tables
├─ Structured (marks/grades) → SQL
└─ Unstructured (remarks) → Vector DB
```

### RAG Query
```
User Question → Embed → Retrieve Ordinances (Vector DB)
→ Fetch Student Data (SQL) → LLM Reasoning → Answer
```

---

## 📚 API Docs

Visit http://localhost:8000/docs when backend is running.

**Key Endpoints:**
- `POST /api/auth/login`
- `GET /api/eligibility/{student_id}`
- `POST /api/chat`

---

## 🧪 Testing

```bash
cd backend
pytest
python -m agents.eligibility_agent  # Test individual agent
```

---

**Built for AMU ZHCET** 🎓


# To run the project
./run_backend.bat
./run_frontend.bat
=======
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
>>>>>>> 5be736953f63faf8fc0ead525c8dc008ff389a44
