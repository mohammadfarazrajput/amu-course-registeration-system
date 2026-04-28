"""
Eligibility Agent
Analyzes student eligibility using business rules only.
LLM is NOT used here — all data is structured and deterministic.
LLM is reserved for the chat interface (graph.py).
"""

from typing import Dict, List
from sqlalchemy.orm import Session
from models import Student, AcademicRecord, Course
from business_rules import (
    check_promotion_eligibility,
    check_name_removal_risk,
    check_advance_eligibility,
    MIN_CGPA_FOR_ADVANCE,
    MAX_CREDITS_PER_SEMESTER
)


class EligibilityAgent:
    """Analyzes student eligibility using business rules"""

    def __init__(self, db: Session):
        self.db = db

    def analyze_eligibility(self, student_id: int) -> Dict:
        """
        Comprehensive eligibility analysis — pure rule-based, no LLM.
        """
        student = self.db.query(Student).filter(Student.id == student_id).first()
        if not student:
            return {"error": "Student not found"}

        records = self.db.query(AcademicRecord).filter(
            AcademicRecord.student_id == student_id
        ).all()

        sem_credits = {}
        for r in records:
            status_val = str(r.status or "")
            if status_val.upper() == "PASSED":
                course = self.db.query(Course).filter(Course.id == r.course_id).first()
                if course:
                    sem_credits[r.semester] = sem_credits.get(r.semester, 0) + course.credits

        can_promote, promo_reason = check_promotion_eligibility(
            student.current_semester,
            student.total_earned_credits,
            sem_credits
        )

        risk_level, action, risk_msg = check_name_removal_risk(student.not_promoted_count)

        backlogs = self._get_backlogs(records)
        has_backlogs = len(backlogs) > 0

        can_advance, adv_reason = check_advance_eligibility(
            student.current_semester,
            student.cgpa,
            has_backlogs
        )

        allowed_types = []
        if risk_level != "CRITICAL":
            allowed_types.append("CURRENT")
        if has_backlogs:
            allowed_types.append("BACKLOG")
        if can_advance:
            allowed_types.append("ADVANCE")

        warnings = []
        if risk_level != "LOW":
            warnings.append(risk_msg)
        if has_backlogs:
            warnings.append(f"You have {len(backlogs)} backlog course(s)")

        recommendations = self._build_recommendations(
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
        backlogs = []
        course_attempts = {}

        for r in records:
            if r.course_id not in course_attempts:
                course_attempts[r.course_id] = []
            course_attempts[r.course_id].append(r)

        FAIL_GRADES = {"E", "F", "e", "f"}

        for course_id, attempts in course_attempts.items():
            latest = max(attempts, key=lambda x: x.attempt_number)
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

    def _build_recommendations(
        self,
        student: Student,
        can_advance: bool,
        has_backlogs: bool,
        risk_level: str,
    ) -> List[str]:
        """Rule-based recommendations — no LLM, derived from AMU ordinance constants."""
        recs = []

        if risk_level == "CRITICAL":
            recs.append("🚨 URGENT: Your name is at risk of removal. Contact your advisor immediately.")
        elif risk_level == "HIGH":
            recs.append("⚠️ Failed to promote twice. One more failure will result in name removal.")
        elif risk_level == "MEDIUM":
            recs.append("⚠️ Not promoted once. Focus on clearing all courses this semester.")

        if has_backlogs:
            recs.append("📚 Prioritise clearing backlog courses before registering for new ones.")

        if can_advance:
            recs.append(f"🚀 Eligible for course advancement (CGPA ≥ {MIN_CGPA_FOR_ADVANCE}, no backlogs).")
        elif student.current_semester in [5, 6]:
            if student.cgpa < MIN_CGPA_FOR_ADVANCE:
                gap = round(MIN_CGPA_FOR_ADVANCE - student.cgpa, 2)
                recs.append(f"📈 Need {gap} more CGPA points to unlock course advancement.")
            elif has_backlogs:
                recs.append("📚 Clear all backlogs to unlock course advancement eligibility.")

        if student.total_earned_credits < 20:
            recs.append(f"📊 Low credits ({student.total_earned_credits}). Register for max {MAX_CREDITS_PER_SEMESTER} credits this semester.")

        if risk_level == "LOW" and not has_backlogs and not recs:
            recs.append("✅ Good standing. Proceed with regular course registration.")

        return recs[:3]


def create_eligibility_agent(db: Session) -> EligibilityAgent:
    return EligibilityAgent(db)
