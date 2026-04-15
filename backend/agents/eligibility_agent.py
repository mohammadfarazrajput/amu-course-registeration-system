"""
Eligibility Agent
Analyzes student eligibility using business rules + RAG
"""

from typing import Dict, List
from sqlalchemy.orm import Session
from models import Student, AcademicRecord, Course
from business_rules import (
    check_promotion_eligibility,
    check_name_removal_risk,
    check_advance_eligibility
)
from services.retriever import retriever
import os
from langchain_google_genai import ChatGoogleGenerativeAI


class EligibilityAgent:
    """Analyzes student eligibility with RAG-powered reasoning"""
    
    def __init__(self, db: Session):
        self.db = db
        
        # Initialize Gemini LLM
        api_key = os.getenv("GEMINI_API_KEY")
        model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")
        
        try:
            self.llm = ChatGoogleGenerativeAI(
                model=model,
                google_api_key=api_key,
                temperature=0.1
            )
        except Exception as e:
            print(f"⚠️ Failed to initialize LLM: {e}")
            self.llm = None
            
    def _invoke_llm(self, prompt: str) -> str:
        """Helper to invoke LLM safely"""
        if not self.llm:
            return "Recommendation system unavailable."
        response = self.llm.invoke(prompt)
        return response.content if hasattr(response, "content") else str(response)
    
    def analyze_eligibility(self, student_id: int) -> Dict:
        """
        Comprehensive eligibility analysis
        Combines SQL data + business rules + RAG reasoning
        """
        # Get student
        student = self.db.query(Student).filter(Student.id == student_id).first()
        if not student:
            return {"error": "Student not found"}
        
        # Get academic records
        records = self.db.query(AcademicRecord).filter(
            AcademicRecord.student_id == student_id
        ).all()
        
        # Calculate semester-wise credits
        sem_credits = {}
        for r in records:
            status_val = str(r.status or "")
            if status_val.upper() == "PASSED":
                course = self.db.query(Course).filter(Course.id == r.course_id).first()
                if course:
                    sem_credits[r.semester] = sem_credits.get(r.semester, 0) + course.credits
        
        # Check promotion
        can_promote, promo_reason = check_promotion_eligibility(
            student.current_semester,
            student.total_earned_credits,
            sem_credits
        )
        
        # Check risk
        risk_level, action, risk_msg = check_name_removal_risk(student.not_promoted_count)
        
        # Get backlogs
        backlogs = self._get_backlogs(records)
        has_backlogs = len(backlogs) > 0
        
        # Check advancement
        can_advance, adv_reason = check_advance_eligibility(
            student.current_semester,
            student.cgpa,
            has_backlogs
        )
        
        # Determine allowed registration types
        allowed_types = []
        if risk_level != "CRITICAL":
            allowed_types.append("CURRENT")
        if has_backlogs:
            allowed_types.append("BACKLOG")
        if can_advance:
            allowed_types.append("ADVANCE")
        
        # Generate warnings
        warnings = []
        if risk_level != "LOW":
            warnings.append(risk_msg)
        if has_backlogs:
            warnings.append(f"You have {len(backlogs)} backlog course(s)")
        
        # Get RAG-enhanced recommendations
        recommendations = self._get_rag_recommendations(
            student, can_advance, has_backlogs, risk_level
        )
        
        return {
            "student_id": student.id,
            "current_semester": student.current_semester,
            "cgpa": student.cgpa,
            "total_earned_credits": student.total_earned_credits,
            "not_promoted_count": student.not_promoted_count,
            "status": "BLOCKED" if risk_level == "CRITICAL" else "ELIGIBLE",
            "can_register": risk_level != "CRITICAL",
            "can_advance": can_advance,
            "has_backlogs": has_backlogs,
            "backlog_count": len(backlogs),
            "allowed_registration_types": allowed_types,
            "warnings": warnings,
            "recommendations": recommendations,
            "risk_level": risk_level,
            "backlog_courses": backlogs,
            "promotion_status": {
                "can_promote": can_promote,
                "reason": promo_reason
            } if student.current_semester % 2 == 0 else None
        }
    
    def _get_backlogs(self, records: List[AcademicRecord]) -> List[Dict]:
        """Extract backlog courses"""
        backlogs = []
        course_attempts = {}

        # Group by course
        for r in records:
            if r.course_id not in course_attempts:
                course_attempts[r.course_id] = []
            course_attempts[r.course_id].append(r)

        # Check latest attempt per course
        FAIL_GRADES = {"E", "F", "e", "f"}

        for course_id, attempts in course_attempts.items():
            latest = max(attempts, key=lambda x: x.attempt_number)

            # Normalise grade to string for comparison (handles enum or plain str)
            grade_val = latest.grade.value if hasattr(latest.grade, "value") else str(latest.grade or "")
            status_val = str(latest.status or "")

            if grade_val in FAIL_GRADES or status_val.upper() in ("FAILED", "DETAINED"):
                course = self.db.query(Course).filter(Course.id == course_id).first()
                if course:
                    backlogs.append({
                        "course_id": course.id,
                        "course_code": course.course_code,
                        "course_name": course.course_name,
                        "credits": course.credits,
                        "semester": course.semester,
                        "attempt_number": latest.attempt_number,
                        "attendance_fulfilled": latest.attendance_fulfilled
                    })

        return backlogs
    
    def _get_rag_recommendations(
        self,
        student: Student,
        can_advance: bool,
        has_backlogs: bool,
        risk_level: str
    ) -> List[str]:
        """Generate RAG-enhanced recommendations"""
        
        # Retrieve relevant ordinance context
        context = ""
        
        if risk_level == "CRITICAL":
            context = retriever.retrieve_promotion_rules()
        elif can_advance:
            context = retriever.retrieve_advancement_rules()
        
        if not context or len(context) < 50:
            # Fallback to rule-based recommendations
            recs = []
            if risk_level == "CRITICAL":
                recs.append("🚨 URGENT: Meet with advisor immediately!")
            elif has_backlogs:
                recs.append("📚 Clear backlog courses this semester")
            if can_advance:
                recs.append("🚀 You can register for advanced courses")
            return recs
        
        # Use LLM to generate personalized recommendations
        prompt = f"""You are an academic advisor for AMU students.

Student Profile:
- Semester: {student.current_semester}
- CGPA: {student.cgpa}
- Earned Credits: {student.total_earned_credits}
- Has Backlogs: {has_backlogs}
- Can Advance: {can_advance}
- Risk Level: {risk_level}

Relevant AMU Ordinances:
{context}

Generate 2-3 specific, actionable recommendations for this student.
Format as bullet points. Be concise and supportive."""

        try:
            response_text = self._invoke_llm(prompt)
            recommendations = response_text.strip().split('\n')
            return [r.strip() for r in recommendations if r.strip() and not r.strip().startswith('#')][:3]
        except Exception:
            # Fallback
            return ["Register for current semester courses", "Maintain CGPA above 7.5"]


# Factory function
def create_eligibility_agent(db: Session) -> EligibilityAgent:
    return EligibilityAgent(db)