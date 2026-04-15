"""
Parse AMU Curriculum PDFs and extract course data
Converts PDF tables to structured JSON
"""

import sys
from pathlib import Path
import json
import re
import pdfplumber

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

# PDF paths
PDF_DIR = Path(__file__).parent.parent / "data" / "raw" / "curriculum"

# Branch curriculum files
CURRICULUM_FILES = {
    "AI": "AI_effective_from_2023.pdf",
    "CE": "CE_effective_from_2023.pdf",
    "ME": "ME_effective_from_2023.pdf",
    "EE": "EE_effective_from_2023.pdf",
    "AE": "AE_effective_from_2023.pdf",
    "PE": "PE_effective_from_2023.pdf",  # Computer Engineering
    "LE": "LE_effective_from_2023.pdf",  # Electronics
    "KE": "KE_effective_from_2023.pdf",  # Chemical
    "FT": "FT_effective_from_2023.pdf",  # Food Tech
    "PK": "PK_effective_from_2023.pdf",  # Petrochemical
}

# First year common curriculum
FIRST_YEAR_FILE = "1_First_Year_effective_from_2023.pdf"


def parse_course_code(code_str):
    """Parse course code and extract metadata"""
    # Format: XXCYNNN where XX=dept, C=category, Y=year, NNN=number
    if not code_str or len(code_str) < 7:
        return None
    
    match = re.match(r'^([A-Z]{2,3})([A-Z])(\d)(\d{2,3})(\d?)$', code_str)
    if not match:
        return None
    
    dept, category, year, number, version = match.groups()
    
    # Determine course type
    num_int = int(number)
    if num_int >= 90:
        course_type = "lab"
    elif 80 <= num_int < 90:
        course_type = "seminar"
    else:
        course_type = "theory"
    

    return {
        "department": dept,
        "category": category,
        "year": int(year),
        "number": number,
        "version": version or "0",
        "type": course_type
    }


def parse_semester_from_text(text):
    """Extract semester number from text (digits or roman numerals)"""
    if not text:
        return None
    
    # Try digit first
    # e.g. "Semester 3", "Semester-3", "Semester: 3", "Third Semester"
    
    # Look for "Semester X" pattern
    match = re.search(r'(?:Semester|Sem)[-:\s]+(\d+)', text, re.IGNORECASE)
    if match:
        return int(match.group(1))
    
    # Look for Roman numerals
    # e.g. "Semester III", "Semester-IV"
    match = re.search(r'(?:Semester|Sem)[-:\s]+([IVX]+)\b', text, re.IGNORECASE)
    if match:
        roman = match.group(1).upper()
        romans = {
            'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5, 
            'VI': 6, 'VII': 7, 'VIII': 8, 'IX': 9, 'X': 10
        }
        return romans.get(roman)
    
    # Look for ordinal words
    # e.g. "Third Semester"
    ordinals = {
        'first': 1, 'second': 2, 'third': 3, 'fourth': 4, 
        'fifth': 5, 'sixth': 6, 'seventh': 7, 'eighth': 8
    }
    for word, num in ordinals.items():
        if re.search(rf'\b{word}\s+semester\b', text, re.IGNORECASE):
            return num
            
    return None


def extract_courses_from_pdf(pdf_path, branch):
    """Extract courses from curriculum PDF"""
    courses = []
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            current_semester = None
            
            for page_num, page in enumerate(pdf.pages, 1):
                # Try to detect semester from page text
                text = page.extract_text() or ""
                page_sem = parse_semester_from_text(text)
                
                if page_sem:
                    current_semester = page_sem

                
                # Extract tables
                tables = page.extract_tables()
                
                for table in tables:
                    if not table or len(table) < 2:
                        continue
                    
                    # Look for semester indicator in table explicitly
                    table_semester = None
                    for row in table[:3]:
                        row_text = ' '.join([str(cell) for cell in row if cell])
                        sem = parse_semester_from_text(row_text)
                        if sem:
                            table_semester = sem
                            break
                    
                    # Use table semester if found, else fallback to page/current semester
                    semester = table_semester if table_semester else current_semester
                    
                    if not semester:
                        # Try to detect from previous rows

                        continue
                    
                    
                    # Parse course rows
                    

                    
                    # Parse course rows
                    for row in table[1:]:  # Skip header
                        if len(row) < 5:
                            continue
                        
                        # Try to extract course data
                        course_code = None
                        course_name = None
                        credits = None
                        L, T, P = 0, 0, 0
                        category = None
                        
                        for i, cell in enumerate(row):
                            if not cell:
                                continue
                            
                            cell_str = str(cell).strip()

                            
                            # Course code (e.g., AIC2022)
                            if re.match(r'^[A-Z]{2,3}[A-Z]\d{4,5}$', cell_str):

                                course_code = cell_str
                                code_info = parse_course_code(cell_str)
                                if code_info:
                                    category = code_info['category']
                            
                            # Course name (usually long text)
                            elif len(cell_str) > 10 and not re.match(r'^\d+$', cell_str):
                                if not course_name or len(cell_str) > len(course_name):
                                    course_name = cell_str
                            
                            # Credits (single digit 1-9)
                            elif re.match(r'^\d$', cell_str):
                                val = int(cell_str)
                                if 1 <= val <= 9:
                                    if credits is None:
                                        credits = val
                        
                        # Try to extract L-T-P from row
                        ltp_str = ' '.join([str(c) for c in row if c])
                        ltp_match = re.search(r'(\d+)\s+(\d+)\s+(\d+)', ltp_str)
                        if ltp_match:
                            L, T, P = map(int, ltp_match.groups())
                        
                        # Add course if we have minimum data
                        if course_code and credits:
                            # Determine if lab
                            is_lab = P > 0 and L == 0 and T <= 1
                            is_theory = not is_lab
                            
                            course = {
                                "course_code": course_code,
                                "course_name": course_name or course_code,
                                "branch": branch,
                                "semester": semester,
                                "credits": credits,
                                "lecture_hours": L,
                                "tutorial_hours": T,
                                "practical_hours": P,
                                "category": category or "PC",
                                "is_theory": is_theory,
                                "is_lab": is_lab,
                                "is_elective": category in ["PE", "DE", "OE", "E"]
                            }
                            courses.append(course)
    
    except Exception as e:
        print(f"Error processing {pdf_path}: {e}")
    
    return courses


def parse_all_curricula():
    """Parse all curriculum PDFs"""
    all_courses = []
    
    print("🔍 Parsing AMU Curriculum PDFs...")
    
    # Parse each branch
    for branch, filename in CURRICULUM_FILES.items():
        pdf_path = PDF_DIR / filename
        
        if not pdf_path.exists():
            # Try alternate location
            pdf_path = Path("/mnt/user-data/uploads") / filename
        
        if not pdf_path.exists():
            print(f"⚠️  File not found: {filename}")
            continue
        
        print(f"📄 Parsing {branch}: {filename}")
        courses = extract_courses_from_pdf(pdf_path, branch)
        print(f"   ✅ Extracted {len(courses)} courses")
        
        all_courses.extend(courses)
    
    # Parse first year common courses
    first_year_path = PDF_DIR / FIRST_YEAR_FILE
    if not first_year_path.exists():
        first_year_path = Path("/mnt/user-data/uploads") / FIRST_YEAR_FILE
    
    if first_year_path.exists():
        print(f"📄 Parsing First Year Common")
        first_year_courses = extract_courses_from_pdf(first_year_path, "COMMON")
        print(f"   ✅ Extracted {len(first_year_courses)} courses")
        all_courses.extend(first_year_courses)
    
    print(f"\n✅ Total courses extracted: {len(all_courses)}")
    
    # Remove duplicates
    unique_courses = {}
    for course in all_courses:
        code = course['course_code']
        if code not in unique_courses:
            unique_courses[code] = course
        else:
            # Keep the one with more information
            if len(course['course_name']) > len(unique_courses[code]['course_name']):
                unique_courses[code] = course
    
    unique_list = list(unique_courses.values())
    print(f"✅ Unique courses: {len(unique_list)}")
    
    return unique_list


def save_courses_json(courses):
    """Save courses to JSON file"""
    output_dir = Path(__file__).parent.parent / "data" / "processed"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / "courses.json"
    
    with open(output_file, 'w') as f:
        json.dump(courses, f, indent=2)
    
    print(f"💾 Saved to: {output_file}")
    
    # Also save by branch
    by_branch = {}
    for course in courses:
        branch = course['branch']
        if branch not in by_branch:
            by_branch[branch] = []
        by_branch[branch].append(course)
    
    for branch, branch_courses in by_branch.items():
        branch_file = output_dir / f"{branch}_courses.json"
        with open(branch_file, 'w') as f:
            json.dump(branch_courses, f, indent=2)
        print(f"   📁 {branch}: {len(branch_courses)} courses")


if __name__ == "__main__":
    print("=" * 60)
    print("AMU Curriculum Parser")
    print("=" * 60)
    
    courses = parse_all_curricula()
    
    if courses:
        save_courses_json(courses)
        
        # Show statistics
        print("\n📊 Statistics:")
        by_semester = {}
        for c in courses:
            sem = c['semester']
            by_semester[sem] = by_semester.get(sem, 0) + 1
        
        for sem in sorted(by_semester.keys()):
            print(f"   Semester {sem}: {by_semester[sem]} courses")
    else:
        print("❌ No courses extracted!")