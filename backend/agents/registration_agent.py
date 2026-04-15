"""
Registration Agent
Handles course registration submission and validation
"""

from typing import Dict, List
from sqlalchemy.orm import Session
from datetime import datetime
from models import Student, Course, Registration
from schemas import RegistrationModeEnum, RegistrationTypeEnum, RegistrationStatusEnum
from business_rules import validate_credit_limit


class RegistrationAgent:
    """Handles course registration logic"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def submit_registration(
        self,
        student_id: int,
        course_ids: List[int],
        registration_mode: str = "a"
    ) -> Dict:
        """
        Submit course registration
        
        Args:
            student_id: Student ID
            course_ids: List of course IDs to register
            registration_mode: Mode (a/b/c)
        
        Returns:
            Dict with registration status
        """
        # Validate student
        student = self.db.query(Student).filter(Student.id == student_id).first()
        if not student:
            return {
                "success": False,
                "message": "Student not found",
                "errors": ["Invalid student ID"]
            }
        
        # Validate courses exist
        courses = self.db.query(Course).filter(Course.id.in_(course_ids)).all()
        if len(courses) != len(course_ids):
            return {
                "success": False,
                "message": "Invalid course IDs",
                "errors": ["One or more courses not found"]
            }
        
        # Validate credit limit
        course_credits = [c.credits for c in courses]
        is_valid, msg = validate_credit_limit(course_credits)
        if not is_valid:
            return {
                "success": False,
                "message": msg,
                "errors": ["Credit limit exceeded"]
            }
        
        # Validate registration mode
        try:
            mode = RegistrationModeEnum(registration_mode)
        except ValueError:
            return {
                "success": False,
                "message": "Invalid registration mode",
                "errors": ["Mode must be 'a', 'b', or 'c'"]
            }
        
        # Create registrations
        registration_ids = []
        try:
            for course_id in course_ids:
                reg = Registration(
                    student_id=student_id,
                    course_id=course_id,
                    semester=student.current_semester,
                    registration_type=RegistrationTypeEnum.CURRENT,
                    registration_mode=mode,
                    status=RegistrationStatusEnum.CONFIRMED,
                    confirmed_at=datetime.utcnow()
                )
                self.db.add(reg)
                self.db.flush()
                registration_ids.append(reg.id)
            
            self.db.commit()
            
            total_credits = sum(c.credits for c in courses)
            
            return {
                "success": True,
                "message": f"Successfully registered for {len(course_ids)} courses",
                "registration_ids": registration_ids,
                "total_credits": total_credits,
                "errors": []
            }
        
        except Exception as e:
            self.db.rollback()
            return {
                "success": False,
                "message": "Registration failed",
                "errors": [str(e)]
            }
    
    def get_registration_status(self, student_id: int) -> Dict:
        """Get current semester registration status"""
        student = self.db.query(Student).filter(Student.id == student_id).first()
        if not student:
            return {"error": "Student not found"}
        
        # Get registrations for current semester
        registrations = self.db.query(Registration).filter(
            Registration.student_id == student_id,
            Registration.semester == student.current_semester
        ).all()
        
        registered_courses = []
        total_credits = 0
        
        for reg in registrations:
            course = self.db.query(Course).filter(Course.id == reg.course_id).first()
            if course:
                registered_courses.append({
                    "course_code": course.course_code,
                    "course_name": course.course_name,
                    "credits": course.credits,
                    "registration_type": reg.registration_type.value if hasattr(reg.registration_type, 'value') else reg.registration_type,
                    "registration_mode": reg.registration_mode.value if hasattr(reg.registration_mode, 'value') else reg.registration_mode,
                    "status": reg.status.value if hasattr(reg.status, 'value') else reg.status
                })
                total_credits += course.credits
        
        return {
            "student_id": student_id,
            "semester": student.current_semester,
            "registered_courses": registered_courses,
            "total_credits": total_credits,
            "registration_count": len(registered_courses)
        }


# Factory function
def create_registration_agent(db: Session) -> RegistrationAgent:
    return RegistrationAgent(db)