"""
Verification Agent
Handles student authentication and verification
"""

from typing import Dict
from sqlalchemy.orm import Session
from models import Student


class VerificationAgent:
    """Verifies student credentials"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def verify_student(self, faculty_number: str, enrollment_number: str) -> Dict:
        """Verify student credentials"""
        student = self.db.query(Student).filter(
            Student.faculty_number == faculty_number,
            Student.enrollment_number == enrollment_number
        ).first()
        
        if not student:
            return {
                "verified": False,
                "message": "Invalid credentials",
                "student": None
            }
        
        return {
            "verified": True,
            "message": f"Welcome, {student.name}!",
            "student": {
                "id": student.id,
                "name": student.name,
                "faculty_number": student.faculty_number,
                "branch": student.branch,
                "current_semester": student.current_semester,
                "cgpa": student.cgpa,
                "total_earned_credits": student.total_earned_credits
            }
        }
    def get_student_by_id(self, student_id: int) -> dict:
        """Fetch student data by primary key — used by graph.py orchestrator."""
        student = self.db.query(Student).filter(Student.id == student_id).first()
        if not student:
            return {"found": False, "student": None}
        return {
            "found": True,
            "student": {
                "id": student.id,
                "name": student.name,
                "faculty_number": student.faculty_number,
                "enrollment_number": student.enrollment_number,
                "branch": student.branch,
                "current_semester": student.current_semester,
                "cgpa": student.cgpa,
                "sgpa": student.sgpa,
                "total_earned_credits": student.total_earned_credits,
                "not_promoted_count": student.not_promoted_count,
            }
        }
