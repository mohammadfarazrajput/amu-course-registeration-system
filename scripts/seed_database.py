"""
Seed Database with Courses and Sample Students
Populates SQLite database with parsed curriculum data
"""

import sys
from pathlib import Path
import json
import random
from datetime import datetime

sys.path.append(str(Path(__file__).parent.parent))

from backend.database import SessionLocal, init_db
from backend.models import Student, Course, AcademicRecord
from backend.models import CourseCategoryEnum, GradeEnum


def load_courses_from_json():
    """Load parsed courses from JSON"""
    json_path = Path(__file__).parent.parent / "data" / "processed" / "courses.json"
    
    if not json_path.exists():
        print(f"❌ Courses JSON not found: {json_path}")
        print("   Run parse_curriculum.py first!")
        return []
    
    with open(json_path, 'r') as f:
        courses = json.load(f)
    
    return courses


def seed_courses(db):
    """Seed courses into database"""
    print("📚 Seeding courses...")
    
    courses_data = load_courses_from_json()
    
    if not courses_data:
        return 0
    
    added = 0
    for course_data in courses_data:
        # Check if exists
        existing = db.query(Course).filter(
            Course.course_code == course_data['course_code']
        ).first()
        
        if existing:
            continue
        
        # Map category
        category = course_data.get('category', 'PC')
        try:
            category_enum = CourseCategoryEnum[category]
        except KeyError:
            category_enum = CourseCategoryEnum.PC
        
        # Create course
        course = Course(
            course_code=course_data['course_code'],
            course_name=course_data['course_name'],
            category=category_enum,
            branch=course_data['branch'],
            semester=course_data['semester'],
            credits=course_data['credits'],
            lecture_hours=course_data.get('lecture_hours', 0),
            tutorial_hours=course_data.get('tutorial_hours', 0),
            practical_hours=course_data.get('practical_hours', 0),
            is_theory=course_data.get('is_theory', True),
            is_lab=course_data.get('is_lab', False),
            is_elective=course_data.get('is_elective', False)
        )
        
        db.add(course)
        added += 1
    
    db.commit()
    print(f"   ✅ Added {added} courses")
    return added


def generate_sample_students(db, count=20):
    """Generate sample students across different branches"""
    print(f"👨‍🎓 Generating {count} sample students...")
    
    branches = ["AI", "CE", "ME", "EE", "AE", "PE", "LE"]
    names = [
        "Ahmed Khan", "Fatima Ali", "Mohammed Rizvi", "Ayesha Malik",
        "Hassan Sheikh", "Zara Ahmed", "Ali Hussain", "Sana Khan",
        "Imran Siddiqui", "Noor Fatima", "Omar Farooq", "Hiba Rahman",
        "Yusuf Azam", "Laiba Ansari", "Bilal Qureshi", "Maryam Javed",
        "Khalid Usman", "Aisha Begum", "Tariq Mahmood", "Safiya Akhtar"
    ]
    
    added = 0
    admission_year = 2023
    
    for i in range(count):
        name = names[i % len(names)]
        branch = branches[i % len(branches)]
        
        # Generate faculty number (format: YYBRANCHBnnn)
        faculty_num = f"{admission_year % 100}{branch}B{i+1:03d}"
        enrollment_num = f"{admission_year}00{i+1:03d}"
        
        # Check if exists
        existing = db.query(Student).filter(
            Student.faculty_number == faculty_num
        ).first()
        
        if existing:
            continue
        
        # Random semester (3-6 for variety)
        current_sem = random.choice([3, 4, 5, 6])
        
        # Random CGPA (5.0-9.5)
        cgpa = round(random.uniform(5.0, 9.5), 2)
        
        # Calculate earned credits (roughly 20-26 per semester)
        credits_per_sem = random.randint(20, 26)
        earned_credits = credits_per_sem * (current_sem - 1) // 2
        
        # Random promotion status
        not_promoted = 0
        if cgpa < 6.5:
            not_promoted = random.choice([0, 1])
        
        student = Student(
            enrollment_number=enrollment_num,
            faculty_number=faculty_num,
            name=name,
            branch=branch,
            current_semester=current_sem,
            admission_year=admission_year,
            cgpa=cgpa,
            sgpa=cgpa,
            total_earned_credits=earned_credits,
            not_promoted_count=not_promoted
        )
        
        db.add(student)
        added += 1
    
    db.commit()
    print(f"   ✅ Added {added} students")
    return added


def generate_academic_records(db):
    """Generate sample academic records for students"""
    print("📊 Generating academic records...")
    
    students = db.query(Student).all()
    courses = db.query(Course).all()
    
    if not students or not courses:
        print("   ⚠️  No students or courses to create records")
        return 0
    
    # Create course lookup by branch and semester
    courses_by_branch = {}
    for course in courses:
        key = (course.branch, course.semester)
        if key not in courses_by_branch:
            courses_by_branch[key] = []
        courses_by_branch[key].append(course)
    
    added = 0
    grades = [GradeEnum.A_PLUS, GradeEnum.A, GradeEnum.B_PLUS, 
              GradeEnum.B, GradeEnum.C, GradeEnum.D]
    grade_points = [10, 9, 8, 7, 6, 5]
    
    for student in students:
        # Get completed semesters
        completed_semesters = list(range(1, student.current_semester))
        
        for sem in completed_semesters:
            # Get courses for this semester and branch
            key = (student.branch, sem)
            sem_courses = courses_by_branch.get(key, [])
            
            # Also check common first year
            if sem <= 2:
                common_key = ("COMMON", sem)
                sem_courses.extend(courses_by_branch.get(common_key, []))
            
            for course in sem_courses:
                # Random grade (weighted towards good grades)
                grade_idx = random.choices(
                    range(len(grades)),
                    weights=[15, 30, 25, 15, 10, 5]
                )[0]
                
                grade = grades[grade_idx]
                gp = grade_points[grade_idx]
                
                # Random marks
                if course.is_lab:
                    marks = random.randint(45, 95)
                else:
                    marks = random.randint(35, 95)
                
                # Check if record already exists
                existing_record = db.query(AcademicRecord).filter(
                    AcademicRecord.student_id == student.id,
                    AcademicRecord.course_id == course.id,
                    AcademicRecord.semester == sem
                ).first()
                
                if existing_record:
                    continue

                record = AcademicRecord(
                    student_id=student.id,
                    course_id=course.id,
                    semester=sem,
                    attempt_number=1,
                    coursework_obtained=marks * 0.15,
                    midsem_obtained=marks * 0.25,
                    endsem_obtained=marks * 0.60,
                    total_marks=marks,
                    grade=grade,
                    grade_points=gp,
                    status="PASSED" if grade != GradeEnum.E else "FAILED",
                    attendance_fulfilled=True,
                    attendance_percentage=random.randint(75, 100)
                )
                
                db.add(record)
                added += 1
    
    db.commit()
    print(f"   ✅ Added {added} academic records")
    return added


def seed_database():
    """Main seeding function"""
    print("=" * 60)
    print("AMU Database Seeder")
    print("=" * 60)
    
    # Initialize database
    print("🔧 Initializing database...")
    init_db()
    
    # Create session
    db = SessionLocal()
    
    try:
        # Seed courses
        courses_added = seed_courses(db)
        
        # Import real students from Excel using import_students script logic
        # For now, we assume import_students.py is run separately or we can call it here if desired.
        # But per request, we are separating concerns. 
        # Actually, let's call import_students here to ensure the full seeding process works.
        
        from scripts.import_students import import_students_to_db
        students_added, updated = import_students_to_db(db)

        # We do NOT generate fake academic records for real students by default anymore
        # unless explicitly asked. The request says "student_csv should contsinn the data related to the studentt only...
        # and we need to set the courses extracted in teh curriculm data"
        
        records_added = 0 # No fake records for now

        print("\n" + "=" * 60)
        print("✅ Database seeding complete!")
        print(f"   📚 Courses: {courses_added}")
        print(f"   👨‍🎓 Students: {students_added} (Updated: {updated})")
        print("=" * 60)
        
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()