
import sys
import pandas as pd
from pathlib import Path
from sqlalchemy.orm import Session
import re

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from backend.database import SessionLocal, init_db
from backend.models import Student

def clean_data(val):
    if pd.isna(val):
        return None
    return str(val).strip()

def import_students_to_db(db_session=None):
    """Import students to database, can be called from other scripts"""
    print("=" * 60)
    print("Importing Students from Excel")
    print("=" * 60)
    
    # Path to student file (check both extensions)
    base_path = Path(__file__).parent.parent / "data" / "raw" / "student_source"
    excel_path = base_path / "students_2023.xlsx.xlsx"
    if not excel_path.exists():
        excel_path = base_path / "students_2023.xlsx"
        
    if not excel_path.exists():
        print(f"❌ Student file not found at: {excel_path}")
        return 0, 0
    
    should_close_session = False
    if db_session is None:
        db = SessionLocal()
        should_close_session = True
    else:
        db = db_session
        
    added = 0
    updated = 0

    try:
        print(f"📂 Reading: {excel_path.name}")
        # Read file
        try:
             df = pd.read_excel(excel_path, header=None)
        except Exception as e:
             print(f"Error reading Excel: {e}")
             return 0, 0
        
        # Heuristic to find header row or data start
        header_row_idx = None
        
        # Look for headers
        for i, row in df.iterrows():
            row_str = " ".join([str(val) for val in row if pd.notna(val)]).lower()
            # Check for standard headers or the specific ones from screenshot (F_No, En_No)
            if ("faculty" in row_str or "f_no" in row_str) and ("enrollment" in row_str or "en_no" in row_str):
                header_row_idx = i
                print(f"   ✅ Found header at row {i}")
                break
        
        if header_row_idx is not None:
            # Reload with header
            df = pd.read_excel(excel_path, header=header_row_idx)
        else:
            print("   ⚠️  Header not found, attempting to infer columns from data patterns")
            # If no header, try to identify columns by data pattern in first few non-empty rows
            pass

        # Normalize columns if we found headers
        col_map = {}
        if header_row_idx is not None:
             for col in df.columns:
                lower_col = str(col).lower().strip()
                if "enrollment" in lower_col or "enrl" in lower_col or "en_no" in lower_col:
                    col_map["enrollment"] = col
                elif "faculty" in lower_col or "fac no" in lower_col or "f_no" in lower_col:
                    col_map["faculty"] = col
                elif "name" in lower_col:
                    col_map["name"] = col
                elif "branch" in lower_col or "course" in lower_col:
                    col_map["branch"] = col
                elif "sem" in lower_col:
                    col_map["semester"] = col

        # If data patterns logic needed (fallback)
        if not col_map and header_row_idx is None:
             # Assume specific column indices based on previous inspection
             # Col 0: Faculty No, Col 1: Enrollment No, Col 2: Name?, Col 3: Branch?
             # Let's verify with regex
             pass 
        
        # Iterate rows
        for idx, row in df.iterrows():
            # Skip rows before data_start_idx if we manually iterating
            if header_row_idx is None and idx < 10: # heuristic skip top matter
                # Check if this row looks like data
                # Faculty No pattern: 2 digits + chars + digits (e.g., 23AIB001)
                fac_val = str(row[0]).strip() if pd.notna(row[0]) else ""
                if not re.match(r'\d{2}[A-Z]{2,4}\d{3}', fac_val):
                    continue
            
            # Extract data
            if col_map:
                enrollment = clean_data(row.get(col_map.get("enrollment")))
                faculty = clean_data(row.get(col_map.get("faculty")))
                name = clean_data(row.get(col_map.get("name")))
                branch_val = clean_data(row.get(col_map.get("branch")))
                semester_val = row.get(col_map.get("semester"))
            else:
                # Fallback indices based on inspection
                # Assuming: 0: Faculty, 1: Enrollment, 2: Name, 3: Branch, 4: Sem
                faculty = clean_data(row[0])
                enrollment = clean_data(row[1])
                name = clean_data(row[2]) if len(row) > 2 else None
                branch_val = clean_data(row[3]) if len(row) > 3 else None
                semester_val = row[4] if len(row) > 4 else 1

            if not enrollment or not faculty:
                continue
                
            # Basic validation
            if len(faculty) < 5: 
                continue

            # Check existing
            student = db.query(Student).filter(Student.faculty_number == faculty).first()
            
            # Normalize Semester
            try:
                semester = int(semester_val)
            except:
                semester = 1 # Default
                
            # Normalize Branch
            branch = branch_val if branch_val else "UNKNOWN"
            
            # Calculate admission year from Faculty No (e.g. 23... -> 2023)
            try:
                adm_year = int("20" + faculty[:2])
            except:
                adm_year = 2023

            if not student:
                student = Student(
                    enrollment_number=enrollment,
                    faculty_number=faculty,
                    name=name or "Unknown",
                    branch=branch,
                    current_semester=semester,
                    admission_year=adm_year,
                    total_earned_credits=0,
                    cgpa=0.0
                )
                db.add(student)
                added += 1
            else:
                # Update info if mismatch
                if student.name != name and name:
                     student.name = name
                updated += 1
        
        db.commit()
        print(f"✅ Import complete. Added: {added}, Updated: {updated}")
        return added, updated
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 0, 0
    finally:
        if should_close_session:
             db.close()

if __name__ == "__main__":
    import_students_to_db()
