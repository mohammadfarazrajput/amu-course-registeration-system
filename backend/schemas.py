"""
Pydantic Schemas for Request/Response Validation
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime
from enum import Enum


# ==================== ENUMS ====================

class GradeEnum(str, Enum):
    A_PLUS = "A+"
    A = "A"
    B_PLUS = "B+"
    B = "B"
    C = "C"
    D = "D"
    E = "E"
    F = "F"
    I = "I"
    Z = "Z"


class RegistrationTypeEnum(str, Enum):
    CURRENT = "CURRENT"
    BACKLOG = "BACKLOG"
    ADVANCE = "ADVANCE"


class RegistrationModeEnum(str, Enum):
    A = "a"
    B = "b"
    C = "c"


class RegistrationStatusEnum(str, Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"


# ==================== AUTH SCHEMAS ====================

class LoginRequest(BaseModel):
    """Student login request"""
    faculty_number: str = Field(..., min_length=5, max_length=20)
    enrollment_number: str = Field(..., min_length=5, max_length=20)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "faculty_number": "21AIB001",
                "enrollment_number": "202100101"
            }
        }
    )


class LoginResponse(BaseModel):
    """Student login response"""
    verified: bool
    message: str
    student: Optional[dict] = None
    
    model_config = ConfigDict(from_attributes=True)


# ==================== STUDENT SCHEMAS ====================

class StudentBase(BaseModel):
    """Base student schema"""
    enrollment_number: str
    faculty_number: str
    name: str
    branch: str
    current_semester: int
    admission_year: int


class StudentCreate(StudentBase):
    """Schema for creating student"""
    cgpa: Optional[float] = 0.0
    total_earned_credits: Optional[int] = 0
    not_promoted_count: Optional[int] = 0


class StudentResponse(StudentBase):
    """Student response schema"""
    id: int
    cgpa: float
    sgpa: float
    total_earned_credits: int
    not_promoted_count: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ==================== COURSE SCHEMAS ====================

class CourseBase(BaseModel):
    """Base course schema"""
    course_code: str
    course_name: str
    category: str
    branch: str
    semester: int
    credits: int


class CourseCreate(CourseBase):
    """Schema for creating course"""
    lecture_hours: Optional[int] = 0
    tutorial_hours: Optional[int] = 0
    practical_hours: Optional[int] = 0
    is_theory: Optional[bool] = True
    is_lab: Optional[bool] = False
    prerequisites: Optional[str] = None


class CourseResponse(CourseBase):
    """Course response schema"""
    id: int
    lecture_hours: int
    tutorial_hours: int
    practical_hours: int
    is_theory: bool
    is_lab: bool
    is_elective: bool
    prerequisites: Optional[str]
    
    model_config = ConfigDict(from_attributes=True)


class CourseRecommendation(BaseModel):
    """Course recommendation with metadata"""
    course_id: int
    course_code: str
    course_name: str
    category: str
    credits: int
    is_theory: bool
    prerequisites: Optional[str]
    prerequisites_met: bool
    registration_type: str  # CURRENT, BACKLOG, ADVANCE
    reason: Optional[str] = None


# ==================== ACADEMIC RECORD SCHEMAS ====================

class AcademicRecordBase(BaseModel):
    """Base academic record schema"""
    student_id: int
    course_id: int
    semester: int
    grade: Optional[GradeEnum] = None


class AcademicRecordCreate(AcademicRecordBase):
    """Schema for creating academic record"""
    coursework_obtained: Optional[float] = 0
    midsem_obtained: Optional[float] = 0
    endsem_obtained: Optional[float] = 0
    total_marks: Optional[float] = 0
    attendance_fulfilled: Optional[bool] = False
    attendance_percentage: Optional[float] = 0


class AcademicRecordResponse(AcademicRecordBase):
    """Academic record response schema"""
    id: int
    attempt_number: int
    coursework_obtained: float
    midsem_obtained: float
    endsem_obtained: float
    total_marks: float
    grade_points: float
    status: str
    attendance_fulfilled: bool
    attendance_percentage: float
    
    model_config = ConfigDict(from_attributes=True)


# ==================== REGISTRATION SCHEMAS ====================

class RegistrationCreate(BaseModel):
    """Schema for course registration"""
    student_id: int
    course_ids: List[int] = Field(..., min_length=1)
    registration_mode: RegistrationModeEnum = RegistrationModeEnum.A
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "student_id": 1,
                "course_ids": [1, 2, 3],
                "registration_mode": "a"
            }
        }
    )


class RegistrationResponse(BaseModel):
    """Registration response"""
    success: bool
    message: str
    registration_ids: Optional[List[int]] = None
    total_credits: Optional[int] = None
    
    model_config = ConfigDict(from_attributes=True)


class RegistrationStatusResponse(BaseModel):
    """Current registration status"""
    student_id: int
    semester: int
    registered_courses: List[dict]
    total_credits: int
    registration_count: int


# ==================== ELIGIBILITY SCHEMAS ====================

class EligibilityResponse(BaseModel):
    """Eligibility analysis response"""
    student_id: int
    current_semester: int
    cgpa: float
    total_earned_credits: int
    not_promoted_count: int
    status: str  # ELIGIBLE, BLOCKED
    can_register: bool
    can_advance: bool
    has_backlogs: bool
    backlog_count: int
    allowed_registration_types: List[str]
    warnings: List[str]
    errors: List[str]
    recommendations: List[str]
    risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL
    promotion_status: Optional[dict] = None
    backlog_courses: Optional[List[dict]] = None


# ==================== CHAT SCHEMAS ====================

class ChatMessage(BaseModel):
    """Chat message schema"""
    student_id: int
    message: str = Field(..., min_length=1, max_length=2000)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "student_id": 1,
                "message": "Can I register for advanced courses?"
            }
        }
    )


class ChatResponse(BaseModel):
    """Chat response schema"""
    response: str
    context: Optional[dict] = None
    sources: Optional[List[str]] = None  # For RAG citations


class ChatHistoryResponse(BaseModel):
    """Chat history response"""
    history: List[dict]


# ==================== DOCUMENT UPLOAD SCHEMAS ====================

class DocumentUploadResponse(BaseModel):
    """Document upload response"""
    success: bool
    message: str
    file_path: Optional[str] = None
    document_id: Optional[int] = None
    extracted_data: Optional[dict] = None


# ==================== COURSE RECOMMENDATION SCHEMAS ====================

class CourseRecommendationRequest(BaseModel):
    """Request for course recommendations"""
    student_id: int
    include_backlogs: bool = True
    include_advance: bool = True


class CourseRecommendationResponse(BaseModel):
    """Course recommendations response"""
    student_id: int
    semester: int
    courses: dict  # {current: [], backlogs: [], advance: []}
    total_credits: int
    summary: dict
    warning: Optional[str] = None


# ==================== UTILITY SCHEMAS ====================

class HealthCheckResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: datetime
    database: str
    vector_store: Optional[str] = None


class ErrorResponse(BaseModel):
    """Error response schema"""
    detail: str
    error_code: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)