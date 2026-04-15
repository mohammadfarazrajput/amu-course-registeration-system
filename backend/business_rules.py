"""
AMU B.Tech Business Rules Implementation
Based on AMU Ordinances 2023-24
"""

from typing import Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class PromotionRequirement:
    """Promotion requirements for different semesters"""
    semester: int
    min_earned_credits: int
    special_conditions: str = ""


# ==================== AMU CONSTANTS ====================

# Clause 11.1: Promotion Requirements
PROMOTION_REQUIREMENTS = {
    2: PromotionRequirement(
        semester=2,
        min_earned_credits=16,
        special_conditions="Minimum 16 credits"
    ),
    4: PromotionRequirement(
        semester=4,
        min_earned_credits=60,
        special_conditions="Including at least 36 credits from first two semesters"
    ),
    6: PromotionRequirement(
        semester=6,
        min_earned_credits=108,
        special_conditions="Including at least 80 credits from first four semesters"
    )
}

# Name removal threshold
MAX_NOT_PROMOTED_COUNT = 3  # Clause 11.1

# Advancement eligibility
MIN_CGPA_FOR_ADVANCE = 7.5  # Clause 7.2 j
ADVANCE_ELIGIBLE_SEMESTERS = [5, 6]  # III year only

# Credit limits
MAX_CREDITS_PER_SEMESTER = 40  # Clause 7.1 e
MIN_PASSING_GRADE_THEORY = "D"  # 35 marks
MIN_PASSING_GRADE_LAB = "C"  # 45 marks

# Grade points mapping
GRADE_POINTS = {
    "A+": 10,
    "A": 9,
    "B+": 8,
    "B": 7,
    "C": 6,
    "D": 5,
    "E": 0,
    "F": 0,
    "I": 0,
    "Z": 0
}

# Passing grades
PASSING_GRADES_THEORY = ["A+", "A", "B+", "B", "C", "D"]
PASSING_GRADES_LAB = ["A+", "A", "B+", "B", "C"]


# ==================== BUSINESS LOGIC FUNCTIONS ====================

def check_promotion_eligibility(
    current_semester: int,
    total_earned_credits: int,
    semester_wise_credits: Dict[int, int]
) -> Tuple[bool, str]:
    """
    Check if student meets promotion requirements
    
    Args:
        current_semester: Student's current semester
        total_earned_credits: Total credits earned so far
        semester_wise_credits: Dict mapping semester -> earned credits
    
    Returns:
        (is_promoted, reason)
    """
    # Only check at even semesters
    if current_semester not in PROMOTION_REQUIREMENTS:
        return True, "Promotion check only at even semesters"
    
    req = PROMOTION_REQUIREMENTS[current_semester]
    
    # Check total credits
    if total_earned_credits < req.min_earned_credits:
        return False, f"Insufficient credits: {total_earned_credits}/{req.min_earned_credits}"
    
    # Special check for Semester 4
    if current_semester == 4:
        first_two_sem_credits = semester_wise_credits.get(1, 0) + semester_wise_credits.get(2, 0)
        if first_two_sem_credits < 36:
            return False, f"Need 36 credits from first two semesters. Current: {first_two_sem_credits}"
    
    # Special check for Semester 6
    if current_semester == 6:
        first_four_sem_credits = sum(semester_wise_credits.get(i, 0) for i in range(1, 5))
        if first_four_sem_credits < 80:
            return False, f"Need 80 credits from first four semesters. Current: {first_four_sem_credits}"
    
    return True, f"Promotion eligible: {total_earned_credits}/{req.min_earned_credits} credits"


def check_name_removal_risk(not_promoted_count: int) -> Tuple[str, str, str]:
    """
    Check if student is at risk of name removal
    
    Returns:
        (risk_level, action, message)
    """
    if not_promoted_count >= MAX_NOT_PROMOTED_COUNT:
        return "CRITICAL", "NAME_REMOVAL", \
               f"⛔ Name will be removed! Not promoted {not_promoted_count} times (max: {MAX_NOT_PROMOTED_COUNT})"
    elif not_promoted_count == 2:
        return "HIGH", "WARNING", \
               "⚠️ WARNING: Not promoted 2 times. One more failure → Name removal!"
    elif not_promoted_count == 1:
        return "MEDIUM", "CAUTION", \
               "⚠️ CAUTION: Not promoted once. Be careful!"
    else:
        return "LOW", "SAFE", "Good standing"


def check_advance_eligibility(
    current_semester: int,
    cgpa: float,
    has_backlogs: bool
) -> Tuple[bool, str]:
    """
    Check if student can register for advanced courses
    Clause 7.2 j: III year students with CGPA ≥ 7.5, no backlogs
    
    Returns:
        (is_eligible, reason)
    """
    if current_semester not in ADVANCE_ELIGIBLE_SEMESTERS:
        return False, "Advancement only for III year students (Sem 5/6)"
    
    if cgpa < MIN_CGPA_FOR_ADVANCE:
        return False, f"CGPA must be ≥ {MIN_CGPA_FOR_ADVANCE}. Current: {cgpa}"
    
    if has_backlogs:
        return False, "Cannot advance with pending backlogs"
    
    return True, f"✅ Eligible for advancement (CGPA: {cgpa}, No backlogs)"


def get_registration_mode_rules(mode: str, is_lab: bool) -> Dict[str, any]:
    """
    Get rules for different registration modes (Clause 7.1)
    
    Returns:
        Dict with mode requirements
    """
    modes = {
        "a": {
            "name": "Mode A",
            "description": "Full attendance + all evaluations",
            "attendance_required": True,
            "all_evaluations": True,
            "applicable_to_lab": True,
            "notes": "Mandatory for first attempt"
        },
        "b": {
            "name": "Mode B",
            "description": "All evaluations, no attendance",
            "attendance_required": False,
            "all_evaluations": True,
            "applicable_to_lab": False,
            "notes": "Only for theory courses if attendance fulfilled earlier"
        },
        "c": {
            "name": "Mode C",
            "description": "End-sem only, sessional marks reused",
            "attendance_required": False,
            "all_evaluations": False,
            "applicable_to_lab": True,
            "notes": "Previous sessional marks considered"
        }
    }
    
    if mode not in modes:
        raise ValueError(f"Invalid mode: {mode}")
    
    mode_info = modes[mode]
    
    # Lab courses cannot use Mode B
    if is_lab and mode == "b":
        raise ValueError("Mode B not applicable for lab courses")
    
    return mode_info


def calculate_grade_points(marks: float, is_lab: bool = False) -> Tuple[str, float]:
    """
    Calculate grade and grade points from marks
    Based on Clause 9.2
    
    Returns:
        (grade, grade_points)
    """
    if is_lab:
        # Lab course grading
        if marks >= 85:
            return "A+", 10
        elif marks >= 75:
            return "A", 9
        elif marks >= 65:
            return "B+", 8
        elif marks >= 55:
            return "B", 7
        elif marks >= 45:
            return "C", 6  # Min passing
        else:
            return "E", 0
    else:
        # Theory course grading
        if marks >= 85:
            return "A+", 10
        elif marks >= 75:
            return "A", 9
        elif marks >= 65:
            return "B+", 8
        elif marks >= 55:
            return "B", 7
        elif marks >= 45:
            return "C", 6
        elif marks >= 35:
            return "D", 5  # Min passing
        else:
            return "E", 0


def calculate_cgpa(grade_credit_list: List[Tuple[str, int]]) -> float:
    """
    Calculate CGPA from list of (grade, credits)
    
    Args:
        grade_credit_list: List of tuples [(grade, credits), ...]
    
    Returns:
        CGPA (0-10)
    """
    total_weighted_points = 0
    total_credits = 0
    
    for grade, credits in grade_credit_list:
        if grade in GRADE_POINTS:
            total_weighted_points += GRADE_POINTS[grade] * credits
            total_credits += credits
    
    if total_credits == 0:
        return 0.0
    
    return round(total_weighted_points / total_credits, 2)


def get_backlog_courses(academic_records: List[Dict]) -> List[Dict]:
    """
    Extract backlog courses from academic records
    
    Args:
        academic_records: List of dicts with keys: course_id, grade, status
    
    Returns:
        List of backlog course info
    """
    backlogs = []
    
    # Group by course_id to find latest attempt
    course_attempts = {}
    for record in academic_records:
        course_id = record['course_id']
        if course_id not in course_attempts:
            course_attempts[course_id] = []
        course_attempts[course_id].append(record)
    
    # Check if latest attempt is a fail
    for course_id, attempts in course_attempts.items():
        latest_attempt = max(attempts, key=lambda x: x.get('attempt_number', 1))
        
        if latest_attempt['grade'] in ['E', 'F'] or latest_attempt['status'] == 'FAILED':
            backlogs.append({
                'course_id': course_id,
                'grade': latest_attempt['grade'],
                'attempt_number': latest_attempt.get('attempt_number', 1),
                'attendance_fulfilled': latest_attempt.get('attendance_fulfilled', False)
            })
    
    return backlogs


def validate_credit_limit(selected_course_credits: List[int]) -> Tuple[bool, str]:
    """
    Check if total credits exceed limit (Clause 7.1 e)
    
    Returns:
        (is_valid, message)
    """
    total_credits = sum(selected_course_credits)
    
    if total_credits > MAX_CREDITS_PER_SEMESTER:
        return False, f"Total credits ({total_credits}) exceed maximum limit of {MAX_CREDITS_PER_SEMESTER}"
    
    return True, f"Valid: {total_credits}/{MAX_CREDITS_PER_SEMESTER} credits"


# ==================== UTILITY FUNCTIONS ====================

def get_branch_from_faculty_number(faculty_number: str) -> str:
    """
    Extract branch code from faculty number
    Format: YYBRANCHNNN (e.g., 21AIB001 → AI)
    """
    try:
        # Extract characters 2-4 or 2-5
        if len(faculty_number) >= 5:
            branch_part = faculty_number[2:5]
            # Remove 'B' if present
            if branch_part.endswith('B'):
                branch_part = branch_part[:-1]
            return branch_part
        return "UNKNOWN"
    except:
        return "UNKNOWN"


def get_semester_from_admission_year(admission_year: int, current_year: int, current_month: int) -> int:
    """
    Calculate current semester based on admission year
    Odd semester: July-December
    Even semester: January-June
    """
    years_diff = current_year - admission_year
    
    # Determine if odd or even semester based on month
    if current_month >= 7:  # July onwards = Odd semester
        semester = (years_diff * 2) + 1
    else:  # January-June = Even semester
        semester = years_diff * 2
    
    return max(1, min(semester, 8))  # Clamp between 1-8