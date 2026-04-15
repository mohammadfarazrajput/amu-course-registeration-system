"""
Course Selector Agent
Recommends courses based on eligibility and curriculum
"""

from typing import Dict, List
from sqlalchemy.orm import Session
from models import Course, AcademicRecord

class CourseSelectorAgent:
    """Selects appropriate courses for registration"""
    
    def __init__(self, db: Session):
        self.db = db
        
    def recommend_courses(self, student_id: int, eligibility: Dict) -> Dict:
        """
        Recommend courses based on eligibility status
        Returns: {
            "student_id": int,
            "semester": int,
            "courses": {
                "current": [],
                "backlogs": [],
                "advance": []
            },
            "total_credits": int,
            "summary": Dict
        }
        """
        
        # Unpack eligibility
        current_sem = eligibility["current_semester"]
        has_backlogs = eligibility["has_backlogs"]
        can_advance = eligibility["can_advance"]
        risk_level = eligibility["risk_level"]
        backlog_list = eligibility.get("backlog_courses", [])
        
        # 1. Get Current Semester Courses (excluding already passed)
        current_courses = self._get_courses_by_semester(current_sem, student_id)

        # 2. Backlog Courses (already identified by eligibility agent)
        backlog_courses = list(backlog_list)

        # 3. Advance Courses (next semester)
        advance_courses = []
        if can_advance:
            advance_courses = self._get_courses_by_semester(current_sem + 1, student_id)
             
        # Filter based on Risk
        if risk_level == "CRITICAL":
            # Only backlogs allowed usually, or minimal load
            current_courses = [] # Block current? Or warn?
            # Typically critical risk means focus on backlogs
            pass
            
        return {
            "student_id": student_id,
            "semester": current_sem,
            "courses": {
                "current": [self._course_to_dict(c) for c in current_courses],
                "backlogs": backlog_courses,
                "advance": [self._course_to_dict(c) for c in advance_courses]
            },
            "total_credits": sum(c.credits for c in current_courses), # Estimate
            "summary": {
                "risk_level": risk_level,
                "can_advance": can_advance,
                "message": self._generate_message(risk_level, len(backlog_courses))
            }
        }
        
    def _get_courses_by_semester(self, semester: int, student_id: int = None) -> List[Course]:
        """Fetch courses for a given semester, excluding already-passed ones
        and filtering legacy/canonical codes by student's admission year batch."""
        from models import Student
        courses = self.db.query(Course).filter(Course.semester == semester).all()

        # Determine student's admission year to pick the right batch curriculum
        adm_year = None
        if student_id:
            s = self.db.query(Student).filter(Student.id == student_id).first()
            if s:
                adm_year = s.admission_year

            # Exclude already-passed courses
            passed_ids = set(
                r.course_id for r in
                self.db.query(AcademicRecord).filter(
                    AcademicRecord.student_id == student_id,
                    AcademicRecord.status == "PASSED"
                ).all()
            )
            courses = [c for c in courses if c.id not in passed_ids]

        return self._deduplicate_courses(courses, adm_year)

    def _deduplicate_courses(self, courses: List[Course], adm_year: int = None) -> List[Course]:
        """Return the right set of courses for this student's batch.
        - batch 2023+: canonical curriculum only (no Legacy)
        - older batches: include legacy codes they actually studied, skip canonical duplicates
        """
        if adm_year and adm_year >= 2023:
            # New curriculum — drop all legacy placeholder courses
            return [c for c in courses if "(Legacy)" not in c.course_name]

        # Older batch: keep legacy codes; if a canonical code covers the same
        # slot drop the legacy duplicate so there's no double-counting.
        canonical_codes = {c.course_code for c in courses if "(Legacy)" not in c.course_name}
        result = []
        for c in courses:
            if "(Legacy)" in c.course_name:
                # Only include if no canonical course already covers this code
                if c.course_code not in canonical_codes:
                    result.append(c)
            else:
                result.append(c)
        return result
        
    def _course_to_dict(self, course: Course) -> Dict:
        """Convert Course model to dict"""
        return {
            "course_id": course.id,
            "course_code": course.course_code,
            "course_name": course.course_name,
            "category": course.category.value if hasattr(course.category, 'value') else course.category,
            "credits": course.credits,
            "semester": course.semester,
            "is_theory": course.is_theory,
            "is_lab": course.is_lab,
            "is_elective": course.is_elective
        }
        
    def _generate_message(self, risk: str, backlog_count: int) -> str:
        if risk == "CRITICAL":
            return "CRITICAL ACADEMIC STANDING. Contact Advisor."
        elif backlog_count > 0:
            return f"You have {backlog_count} backlog courses to clear."
        else:
            return "You are on track. Proceed with registration."

def create_course_selector_agent(db: Session) -> CourseSelectorAgent:
    return CourseSelectorAgent(db)
