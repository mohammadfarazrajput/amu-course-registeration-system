"""
FastAPI Main Application
AMU Course Registration System Backend
"""

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pathlib import Path
from datetime import datetime
from contextlib import asynccontextmanager

from database import get_db, init_db
from models import Student, Course, Registration, ChatHistory, AcademicRecord
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv(Path(__file__).parent.parent / ".env")

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
        print(f"Chat error: {e}")
        fallback = "I'm having trouble right now. Please try again or check the eligibility page."
        
        agent_chat = ChatHistory(
            student_id=message.student_id,
            message=fallback,
            sender="AGENT"
        )
        db.add(agent_chat)
        db.commit()
        
        return {"response": fallback}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)