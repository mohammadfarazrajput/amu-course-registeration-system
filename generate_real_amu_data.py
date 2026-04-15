"""
Real AMU Data Generator
Processes actual AMU student list and curriculum PDFs to create database
"""

import pandas as pd
import random
from pathlib import Path

# Branch code mapping (from faculty numbers)
BRANCH_CODES = {
    'AI': 'Artificial Intelligence',
    'ME': 'Mechanical Engineering',
    'EE': 'Electrical Engineering', 
    'CE': 'Civil Engineering',
    'CO': 'Computer Engineering',
    'EL': 'Electronics Engineering',
    'CH': 'Chemical Engineering',
    'AR': 'Architecture',
    'PK': 'Petrochemical Engineering',
    'FT': 'Food Technology',
    'AE': 'Automobile Engineering'
}

def parse_faculty_number(f_no):
    """
    Parse faculty number to extract admission year and branch
    Format: YYBRANCHXXX (e.g., 23AIBEA103)
    """
    if not f_no or len(f_no) < 5:
        return None, None
    
    year = f_no[:2]  # 23 = 2023
    # Extract branch code (usually 2-3 letters after year)
    branch_part = f_no[2:]
    
    # Try to match branch code
    for code in BRANCH_CODES.keys():
        if code in branch_part[:4].upper():
            return f"20{year}", code
    
    return f"20{year}", None

def calculate_cgpa_and_credits(semester):
    """Generate realistic CGPA and credits based on semester"""
    if semester == 2:
        # First year students
        cgpa = round(random.uniform(5.5, 9.5), 2)
        min_credits = 16
        earned = random.randint(min_credits, 43)
    elif semester == 4:
        # Second year
        cgpa = round(random.uniform(5.0, 9.2), 2)
        min_credits = 60
        earned = random.randint(min_credits, 95)
    elif semester == 6:
        # Third year
        cgpa = round(random.uniform(5.5, 9.0), 2)
        min_credits = 108
        earned = random.randint(min_credits, 147)
    else:  # 8 or 10
        # Final year
        cgpa = round(random.uniform(6.0, 9.3), 2)
        earned = random.randint(140, 180)
    
    # Determine if promoted before
    not_promoted = 0
    if cgpa < 6.0:
        not_promoted = random.choice([1, 2])
    elif cgpa < 6.5:
        not_promoted = random.choice([0, 1])
    
    return cgpa, earned, not_promoted

def generate_real_students_csv():
    """Generate students.csv from real AMU data"""
    
    # Read actual student list
    df = pd.read_excel('/mnt/user-data/uploads/St_List_BTECH__2_.xlsx', header=1)
    df = df[df['F_No'].notna()].copy()
    
    students_data = []
    
    for idx, row in df.iterrows():
        f_no = str(row['F_No'])
        en_no = str(row['En_No']) if pd.notna(row['En_No']) else f"EN{idx:05d}"
        name = str(row['Name']) if pd.notna(row['Name']) else f"Student {idx}"
        branch_name = str(row['Branch']) if pd.notna(row['Branch']) else "Unknown"
        semester = int(row['Sem.']) if pd.notna(row['Sem.']) else 2
        
        # Parse faculty number
        admission_year, branch_code = parse_faculty_number(f_no)
        
        # If can't parse, use branch name
        if not branch_code:
            branch_code = next((k for k, v in BRANCH_CODES.items() if v == branch_name), 'XX')
        
        # Generate academic data
        cgpa, earned_credits, not_promoted = calculate_cgpa_and_credits(semester)
        
        students_data.append({
            'id': idx + 1,
            'enrollment_number': en_no,
            'faculty_number': f_no,
            'name': name,
            'branch': BRANCH_CODES.get(branch_code, branch_name),
            'current_semester': semester,
            'admission_year': admission_year if admission_year else '2023',
            'cgpa': cgpa,
            'total_earned_credits': earned_credits,
            'not_promoted_count': not_promoted
        })
    
    # Save to CSV
    students_df = pd.DataFrame(students_data)
    students_df.to_csv('../data/real_students.csv', index=False)
    
    print(f"✓ Generated {len(students_df)} real students")
    print(f"  Branches: {students_df['branch'].nunique()}")
    print(f"  Distribution:")
    print(students_df['branch'].value_counts())
    
    return students_df

def generate_ai_courses_csv():
    """
    Generate courses CSV for AI branch based on curriculum PDFs
    """
    
    # AI 2023 curriculum (from AI_23_99.pdf and AI_effective_from_2023.pdf)
    courses = [
        # Semester 3
        {'course_code': 'AIC2022', 'course_name': 'Introduction to Artificial Intelligence', 'category': 'PC', 'branch': 'Artificial Intelligence', 'semester': 3, 'credits': 4, 'is_theory': True, 'prerequisites': ''},
        {'course_code': 'AIC2062', 'course_name': 'Data Structure and Algorithm', 'category': 'PC', 'branch': 'Artificial Intelligence', 'semester': 3, 'credits': 4, 'is_theory': True, 'prerequisites': ''},
        {'course_code': 'AIC2072', 'course_name': 'Digital Logic and System Design', 'category': 'PC', 'branch': 'Artificial Intelligence', 'semester': 3, 'credits': 4, 'is_theory': True, 'prerequisites': ''},
        {'course_code': 'AIC2122', 'course_name': 'Database Management System', 'category': 'PC', 'branch': 'Artificial Intelligence', 'semester': 3, 'credits': 4, 'is_theory': True, 'prerequisites': ''},
        {'course_code': 'AIC2922', 'course_name': 'Artificial Intelligence Lab', 'category': 'PC', 'branch': 'Artificial Intelligence', 'semester': 3, 'credits': 2, 'is_theory': False, 'prerequisites': ''},
        {'course_code': 'AMS2612', 'course_name': 'Higher Mathematics', 'category': 'BS', 'branch': 'Artificial Intelligence', 'semester': 3, 'credits': 4, 'is_theory': True, 'prerequisites': ''},
        {'course_code': 'ELA2112', 'course_name': 'Electronic Devices & Circuits', 'category': 'ESA', 'branch': 'Artificial Intelligence', 'semester': 3, 'credits': 4, 'is_theory': True, 'prerequisites': ''},
        
        # Semester 4
        {'course_code': 'AIC2042', 'course_name': 'Principles of Machine Learning', 'category': 'PC', 'branch': 'Artificial Intelligence', 'semester': 4, 'credits': 4, 'is_theory': True, 'prerequisites': 'AIC2022'},
        {'course_code': 'AIC2142', 'course_name': 'Design & Analysis of Algorithm', 'category': 'PC', 'branch': 'Artificial Intelligence', 'semester': 4, 'credits': 4, 'is_theory': True, 'prerequisites': 'AIC2062'},
        {'course_code': 'AIC2152', 'course_name': 'AI Tools & Techniques', 'category': 'PC', 'branch': 'Artificial Intelligence', 'semester': 4, 'credits': 4, 'is_theory': True, 'prerequisites': ''},
        {'course_code': 'AIC2912', 'course_name': 'Data Structure Lab', 'category': 'PC', 'branch': 'Artificial Intelligence', 'semester': 4, 'credits': 2, 'is_theory': False, 'prerequisites': ''},
        {'course_code': 'AIP2922', 'course_name': 'Colloquium', 'category': 'PSI', 'branch': 'Artificial Intelligence', 'semester': 4, 'credits': 2, 'is_theory': False, 'prerequisites': ''},
        {'course_code': 'AMS2632', 'course_name': 'Discrete Structures', 'category': 'BS', 'branch': 'Artificial Intelligence', 'semester': 4, 'credits': 4, 'is_theory': True, 'prerequisites': ''},
        {'course_code': 'ELA2412', 'course_name': 'Fundamentals of Digital Signal Processing', 'category': 'ESA', 'branch': 'Artificial Intelligence', 'semester': 4, 'credits': 4, 'is_theory': True, 'prerequisites': ''},
        {'course_code': 'ELA2902', 'course_name': 'Electronics Laboratory', 'category': 'ESA', 'branch': 'Artificial Intelligence', 'semester': 4, 'credits': 2, 'is_theory': False, 'prerequisites': ''},
        
        # Semester 5
        {'course_code': 'AIC3072', 'course_name': 'AI System Design', 'category': 'PC', 'branch': 'Artificial Intelligence', 'semester': 5, 'credits': 4, 'is_theory': True, 'prerequisites': 'AIC2022'},
        {'course_code': 'AIC3092', 'course_name': 'Microprocessor Theory & Applications', 'category': 'PC', 'branch': 'Artificial Intelligence', 'semester': 5, 'credits': 3, 'is_theory': True, 'prerequisites': ''},
        {'course_code': 'AIC3102', 'course_name': 'Operating Systems', 'category': 'PC', 'branch': 'Artificial Intelligence', 'semester': 5, 'credits': 4, 'is_theory': True, 'prerequisites': ''},
        {'course_code': 'AIC3942', 'course_name': 'Machine Learning Lab', 'category': 'PC', 'branch': 'Artificial Intelligence', 'semester': 5, 'credits': 2, 'is_theory': False, 'prerequisites': 'AIC2042'},
        {'course_code': 'AIP3932', 'course_name': 'Minor Project-I', 'category': 'PSI', 'branch': 'Artificial Intelligence', 'semester': 5, 'credits': 2, 'is_theory': False, 'prerequisites': ''},
        {'course_code': 'ELA3402', 'course_name': 'Communication Systems', 'category': 'ESA', 'branch': 'Artificial Intelligence', 'semester': 5, 'credits': 4, 'is_theory': True, 'prerequisites': ''},
        {'course_code': 'MEH3452', 'course_name': 'Engineering Economy & Management', 'category': 'HM', 'branch': 'Artificial Intelligence', 'semester': 5, 'credits': 3, 'is_theory': True, 'prerequisites': ''},
        {'course_code': 'OEC1001', 'course_name': 'Open Elective-1', 'category': 'OE', 'branch': 'Artificial Intelligence', 'semester': 5, 'credits': 3, 'is_theory': True, 'prerequisites': ''},
        
        # Semester 6
        {'course_code': 'AIC3132', 'course_name': 'Computer Networks', 'category': 'PC', 'branch': 'Artificial Intelligence', 'semester': 6, 'credits': 4, 'is_theory': True, 'prerequisites': ''},
        {'course_code': 'AIC3142', 'course_name': 'Deep Learning', 'category': 'PC', 'branch': 'Artificial Intelligence', 'semester': 6, 'credits': 4, 'is_theory': True, 'prerequisites': 'AIC2042'},
        {'course_code': 'AIC3172', 'course_name': 'Natural Language Processing', 'category': 'PC', 'branch': 'Artificial Intelligence', 'semester': 6, 'credits': 4, 'is_theory': True, 'prerequisites': 'AIC2042'},
        {'course_code': 'AIC3972', 'course_name': 'Deep Learning Lab', 'category': 'PC', 'branch': 'Artificial Intelligence', 'semester': 6, 'credits': 2, 'is_theory': False, 'prerequisites': 'AIC3142'},
        {'course_code': 'AIC3982', 'course_name': 'Microprocessor & Embedded Systems Lab', 'category': 'PC', 'branch': 'Artificial Intelligence', 'semester': 6, 'credits': 2, 'is_theory': False, 'prerequisites': ''},
        {'course_code': 'AIP3952', 'course_name': 'Minor Project-II', 'category': 'PSI', 'branch': 'Artificial Intelligence', 'semester': 6, 'credits': 2, 'is_theory': False, 'prerequisites': 'AIP3932'},
        {'course_code': 'OEC2001', 'course_name': 'Open Elective-2', 'category': 'OE', 'branch': 'Artificial Intelligence', 'semester': 6, 'credits': 3, 'is_theory': True, 'prerequisites': ''},
        {'course_code': 'HMC3001', 'course_name': 'Humanities Elective', 'category': 'HM', 'branch': 'Artificial Intelligence', 'semester': 6, 'credits': 3, 'is_theory': True, 'prerequisites': ''},
        
        # Semester 7
        {'course_code': 'AIC4252', 'course_name': 'Advanced Machine Learning', 'category': 'PC', 'branch': 'Artificial Intelligence', 'semester': 7, 'credits': 4, 'is_theory': True, 'prerequisites': 'AIC2042'},
        {'course_code': 'AIC4972', 'course_name': 'Advanced Artificial Intelligence Lab', 'category': 'PC', 'branch': 'Artificial Intelligence', 'semester': 7, 'credits': 2, 'is_theory': False, 'prerequisites': ''},
        {'course_code': 'AIP4982', 'course_name': 'Project Phase-I', 'category': 'PSI', 'branch': 'Artificial Intelligence', 'semester': 7, 'credits': 4, 'is_theory': False, 'prerequisites': ''},
        {'course_code': 'AIE4010', 'course_name': 'Computer Vision', 'category': 'DE', 'branch': 'Artificial Intelligence', 'semester': 7, 'credits': 3, 'is_theory': True, 'prerequisites': ''},
        {'course_code': 'AIE4020', 'course_name': 'Reinforcement Learning', 'category': 'DE', 'branch': 'Artificial Intelligence', 'semester': 7, 'credits': 3, 'is_theory': True, 'prerequisites': ''},
        {'course_code': 'AIE4030', 'course_name': 'Big Data Analytics', 'category': 'DE', 'branch': 'Artificial Intelligence', 'semester': 7, 'credits': 3, 'is_theory': True, 'prerequisites': ''},
        {'course_code': 'AIE4040', 'course_name': 'Cloud Computing', 'category': 'DE', 'branch': 'Artificial Intelligence', 'semester': 7, 'credits': 3, 'is_theory': True, 'prerequisites': ''},
        
        # Semester 8
        {'course_code': 'AIP4802', 'course_name': 'Industrial Training/Internship', 'category': 'PSI', 'branch': 'Artificial Intelligence', 'semester': 8, 'credits': 2, 'is_theory': False, 'prerequisites': ''},
        {'course_code': 'AIP4992', 'course_name': 'Project Phase-II', 'category': 'PSI', 'branch': 'Artificial Intelligence', 'semester': 8, 'credits': 6, 'is_theory': False, 'prerequisites': 'AIP4982'},
        {'course_code': 'AIE4050', 'course_name': 'Quantum Computing', 'category': 'DE', 'branch': 'Artificial Intelligence', 'semester': 8, 'credits': 3, 'is_theory': True, 'prerequisites': ''},
        {'course_code': 'AIE4060', 'course_name': 'Blockchain Technology', 'category': 'DE', 'branch': 'Artificial Intelligence', 'semester': 8, 'credits': 3, 'is_theory': True, 'prerequisites': ''},
    ]
    
    # Add IDs
    for i, course in enumerate(courses, 1):
        course['id'] = i
    
    courses_df = pd.DataFrame(courses)
    courses_df.to_csv('../data/real_ai_courses.csv', index=False)
    
    print(f"✓ Generated {len(courses_df)} AI courses")
    print(f"  Semesters: {sorted(courses_df['semester'].unique())}")
    print(f"  Categories: {courses_df['category'].unique()}")
    
    return courses_df

if __name__ == "__main__":
    print("=" * 60)
    print("AMU REAL DATA GENERATOR")
    print("=" * 60)
    print()
    
    # Generate real students
    students_df = generate_real_students_csv()
    
    print()
    
    # Generate AI courses
    courses_df = generate_ai_courses_csv()
    
    print()
    print("=" * 60)
    print("✓ COMPLETE! Real AMU data generated")
    print("=" * 60)
