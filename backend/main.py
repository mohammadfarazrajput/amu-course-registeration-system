"""
FastAPI Main Application
AMU Course Registration System Backend
"""

from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pathlib import Path
from datetime import datetime
from contextlib import asynccontextmanager
import httpx

from database import get_db, init_db
from models import Student, Course, Registration, ChatHistory, AcademicRecord
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv(Path(__file__).parent.parent / ".env")
print("GROQ KEY LOADED:", bool(os.getenv("GROQ_API_KEY")))

from schemas import (
    LoginRequest, LoginResponse,
    ChatMessage, ChatResponse,
    RegistrationCreate, RegistrationStatusEnum, RegistrationTypeEnum, RegistrationModeEnum
)
from business_rules import (
    check_promotion_eligibility,
    check_name_removal_risk,
    check_advance_eligibility
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    print("✅ Backend started")
    yield
    # Shutdown
    print("👋 Backend shutdown")


# Initialize FastAPI
app = FastAPI(
    title="AMU Course Registration System",
    description="AI-Powered Registration for ZHCET",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create directories
Path("../data/uploads").mkdir(parents=True, exist_ok=True)


@app.get("/")
async def root():
    return {"status": "healthy", "timestamp": datetime.utcnow()}


@app.post("/api/auth/login")
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    student = db.query(Student).filter(
        Student.faculty_number == request.faculty_number,
        Student.enrollment_number == request.enrollment_number
    ).first()
    
    if not student:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    return {
        "verified": True,
        "message": f"Welcome, {student.name}!",
        "student": {
            "id": student.id,
            "name": student.name,
            "faculty_number": student.faculty_number,
            "enrollment_number": student.enrollment_number,
            "branch": student.branch,
            "current_semester": student.current_semester,
            "cgpa": student.cgpa,
            "total_earned_credits": student.total_earned_credits
        }
    }


@app.get("/api/eligibility/{student_id}")
async def check_eligibility(student_id: int, db: Session = Depends(get_db)):
    from agents.eligibility_agent import create_eligibility_agent

    try:
        agent = create_eligibility_agent(db)
        result = agent.analyze_eligibility(student_id)

        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])

        return result
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"❌ Eligibility error for student {student_id}: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Eligibility check failed: {str(e)}")


@app.get("/api/courses/recommend/{student_id}")
async def recommend_courses(student_id: int, db: Session = Depends(get_db)):
    from agents.eligibility_agent import create_eligibility_agent
    from agents.course_selector import create_course_selector_agent

    try:
        # Get eligibility first
        eligibility_agent = create_eligibility_agent(db)
        eligibility = eligibility_agent.analyze_eligibility(student_id)

        if "error" in eligibility:
            raise HTTPException(status_code=404, detail=eligibility["error"])

        # Get course recommendations
        selector = create_course_selector_agent(db)
        recommendations = selector.recommend_courses(student_id, eligibility)

        if "error" in recommendations:
            raise HTTPException(status_code=404, detail=recommendations["error"])

        return recommendations
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"❌ Course recommendation error for student {student_id}: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Course recommendation failed: {str(e)}")


@app.post("/api/registration/submit")
async def submit_registration(request: RegistrationCreate, db: Session = Depends(get_db)):
    from agents.registration_agent import create_registration_agent
    
    agent = create_registration_agent(db)
    result = agent.submit_registration(
        request.student_id,
        request.course_ids,
        request.registration_mode.value if hasattr(request.registration_mode, 'value') else request.registration_mode
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=400,
            detail=result.get("message", "Registration failed")
        )
    
    return result


@app.post("/api/chat")
async def chat(message: ChatMessage, db: Session = Depends(get_db)):
    from agents.graph import create_orchestrator
    
    # Save user message
    user_chat = ChatHistory(
        student_id=message.student_id,
        message=message.message,
        sender="USER"
    )
    db.add(user_chat)
    db.commit()
    
    # Create orchestrator and get response
    try:
        orchestrator = create_orchestrator(db)
        result = orchestrator.handle_chat(message.student_id, message.message)
        
        response_text = result.get("response", "I couldn't process that request.")
        
        # Save agent response
        agent_chat = ChatHistory(
            student_id=message.student_id,
            message=response_text,
            sender="AGENT",
            agent_type="orchestrator"
        )
        db.add(agent_chat)
        db.commit()
        
        return {
            "response": response_text,
            "context": result.get("context"),
            "sources": result.get("sources", [])
        }
    except Exception as e:
        import traceback
        print(f"Chat error: {e}")
        traceback.print_exc()
        fallback = "I'm having trouble right now. Please try again or check the eligibility page."

        try:
            agent_chat = ChatHistory(
                student_id=message.student_id,
                message=fallback,
                sender="AGENT"
            )
            db.add(agent_chat)
            db.commit()
        except Exception as db_err:
            print(f"⚠️ Could not save fallback chat to DB: {db_err}")
            db.rollback()

        return {"response": fallback}


CERTIFICATE_SERVICE_URL = os.getenv("CERTIFICATE_SERVICE_URL", "http://localhost:8001")


@app.post("/api/certificates/upload")
async def upload_certificate(
    student_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload a student certificate to the certificate extraction service.
    Validates the student exists, forwards the file, extracts data, and persists to DB.
    """
    from models import StudentCertificate
    import json

    # Validate student
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # Validate file type
    allowed_types = {"image/jpeg", "image/png", "image/webp", "application/pdf"}
    content_type = file.content_type or ""
    ext = Path(file.filename or "").suffix.lower()
    ext_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
               ".webp": "image/webp", ".pdf": "application/pdf"}
    resolved_type = ext_map.get(ext, content_type)
    if resolved_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Use PDF, JPG, PNG, or WEBP."
        )

    file_bytes = await file.read()

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{CERTIFICATE_SERVICE_URL}/extract",
                files={"file": (file.filename, file_bytes, resolved_type)},
            )
            response.raise_for_status()
            cert_data = response.json()
    except httpx.ConnectError:
        raise HTTPException(
            status_code=503,
            detail="Certificate service is unavailable. Make sure it is running on port 8001."
        )
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=502,
            detail=f"Certificate service error: {e.response.text}"
        )

    # Persist to local DB
    tags = cert_data.get("suggested_tags") or []
    record = StudentCertificate(
        student_id=student_id,
        filename=file.filename,
        student_name_on_cert=cert_data.get("student_name"),
        organisation=cert_data.get("organisation"),
        event_name=cert_data.get("event_name"),
        event_date=cert_data.get("event_date"),
        issue_date=cert_data.get("issue_date"),
        duration=cert_data.get("duration"),
        primary_category=cert_data.get("primary_category"),
        suggested_tags=json.dumps(tags),
        description=cert_data.get("description"),
        certificate_type=cert_data.get("certificate_type"),
        confidence_score=cert_data.get("confidence_score"),
        category_labels=json.dumps(cert_data.get("category_labels") or {}),
        cert_service_id=cert_data.get("id"),
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return {
        "success": True,
        "student_id": student_id,
        "record_id": record.id,
        "certificate": cert_data
    }


@app.get("/api/certificates/{student_id}")
async def get_certificates(student_id: int, db: Session = Depends(get_db)):
    """Return all uploaded certificates for a student."""
    from models import StudentCertificate
    import json

    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    records = (
        db.query(StudentCertificate)
        .filter(StudentCertificate.student_id == student_id)
        .order_by(StudentCertificate.uploaded_at.desc())
        .all()
    )

    def serialize(r):
        return {
            "id": r.id,
            "filename": r.filename,
            "student_name_on_cert": r.student_name_on_cert,
            "organisation": r.organisation,
            "event_name": r.event_name,
            "event_date": r.event_date,
            "issue_date": r.issue_date,
            "duration": r.duration,
            "primary_category": r.primary_category,
            "suggested_tags": json.loads(r.suggested_tags) if r.suggested_tags else [],
            "description": r.description,
            "certificate_type": r.certificate_type,
            "confidence_score": r.confidence_score,
            "category_labels": json.loads(r.category_labels) if r.category_labels else {},
            "uploaded_at": r.uploaded_at.isoformat() if r.uploaded_at else None,
        }

    return {
        "student_id": student_id,
        "total": len(records),
        "certificates": [serialize(r) for r in records]
    }



if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)