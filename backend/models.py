"""
SQLAlchemy ORM Models
All database models for AMU Registration System
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()


# ==================== ENUMS ====================

class GradeEnum(str, enum.Enum):
    """Grade values as per AMU ordinances"""
    A_PLUS = "A+"
    A = "A"
    B_PLUS = "B+"
    B = "B"
    C = "C"
    D = "D"
    E = "E"  # Fail
    F = "F"  # Detained
    I = "I"  # Incomplete
    Z = "Z"  # Cancelled


class RegistrationModeEnum(str, enum.Enum):
    """Registration modes - AMU Clause 7.1"""
    A = "a"  # Full attendance + evaluations
    B = "b"  # Evaluations only
    C = "c"  # End-sem only


class RegistrationTypeEnum(str, enum.Enum):
    """Course registration types"""
    CURRENT = "CURRENT"
    BACKLOG = "BACKLOG"
    ADVANCE = "ADVANCE"


class RegistrationStatusEnum(str, enum.Enum):
    """Registration status"""
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"


class CourseCategoryEnum(str, enum.Enum):
    """AMU course categories"""
    PC = "PC"  # Programme Core
    PE = "PE"  # Programme Elective
    DC = "DC"  # Departmental Core
    DE = "DE"  # Departmental Elective
    BS = "BS"  # Basic Sciences
    ESA = "ESA"  # Engineering Sciences
    HM = "HM"  # Humanities
    OE = "OE"  # Open Elective
    PSI = "PSI"  # Project/Seminar
    AU = "AU"  # Audit


# ==================== MODELS ====================

class Student(Base):
    """Student master table"""
    __tablename__ = "students"
    
    id = Column(Integer, primary_key=True, index=True)
    enrollment_number = Column(String(20), unique=True, nullable=False, index=True)
    faculty_number = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    branch = Column(String(50), nullable=False)
    current_semester = Column(Integer, nullable=False)
    admission_year = Column(Integer, nullable=False)
    cgpa = Column(Float, default=0.0)
    sgpa = Column(Float, default=0.0)
    total_earned_credits = Column(Integer, default=0)
    not_promoted_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    academic_records = relationship("AcademicRecord", back_populates="student", cascade="all, delete-orphan")
    registrations = relationship("Registration", back_populates="student", cascade="all, delete-orphan")
    chat_history = relationship("ChatHistory", back_populates="student", cascade="all, delete-orphan")


class Course(Base):
    """Course master table"""
    __tablename__ = "courses"
    
    id = Column(Integer, primary_key=True, index=True)
    course_code = Column(String(20), unique=True, nullable=False, index=True)
    course_name = Column(String(200), nullable=False)
    category = Column(Enum(CourseCategoryEnum), nullable=False)
    branch = Column(String(50), nullable=False)
    semester = Column(Integer, nullable=False)
    credits = Column(Integer, nullable=False)
    lecture_hours = Column(Integer, default=0)
    tutorial_hours = Column(Integer, default=0)
    practical_hours = Column(Integer, default=0)
    is_theory = Column(Boolean, default=True)
    is_lab = Column(Boolean, default=False)
    is_elective = Column(Boolean, default=False)
    prerequisites = Column(Text, nullable=True)
    coursework_marks = Column(Integer, default=15)
    midsem_marks = Column(Integer, default=25)
    endsem_marks = Column(Integer, default=60)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    academic_records = relationship("AcademicRecord", back_populates="course")
    registrations = relationship("Registration", back_populates="course")


class AcademicRecord(Base):
    """Student academic performance"""
    __tablename__ = "academic_records"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    semester = Column(Integer, nullable=False)
    attempt_number = Column(Integer, default=1)
    coursework_obtained = Column(Float, default=0)
    midsem_obtained = Column(Float, default=0)
    endsem_obtained = Column(Float, default=0)
    total_marks = Column(Float, default=0)
    grade = Column(Enum(GradeEnum), nullable=True)
    grade_points = Column(Float, default=0)
    status = Column(String(20), default="REGISTERED")
    attendance_fulfilled = Column(Boolean, default=False)
    attendance_percentage = Column(Float, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    student = relationship("Student", back_populates="academic_records")
    course = relationship("Course", back_populates="academic_records")


class Registration(Base):
    """Course registrations"""
    __tablename__ = "registrations"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    semester = Column(Integer, nullable=False)
    registration_type = Column(Enum(RegistrationTypeEnum), nullable=False)
    registration_mode = Column(Enum(RegistrationModeEnum), default=RegistrationModeEnum.A)
    status = Column(Enum(RegistrationStatusEnum), default=RegistrationStatusEnum.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow)
    confirmed_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
    
    # Relationships
    student = relationship("Student", back_populates="registrations")
    course = relationship("Course", back_populates="registrations")


class ChatHistory(Base):
    """Chat conversation history"""
    __tablename__ = "chat_history"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    message = Column(Text, nullable=False)
    sender = Column(String(20), nullable=False)
    agent_type = Column(String(50), nullable=True)
    context = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    student = relationship("Student", back_populates="chat_history")


class Document(Base):
    """Uploaded documents"""
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(50), nullable=False)
    file_size = Column(Integer, nullable=False)
    document_type = Column(String(50), nullable=False)
    processed = Column(Boolean, default=False)
    extracted_data = Column(Text, nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)