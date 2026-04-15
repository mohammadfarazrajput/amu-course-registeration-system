"""
Database Seeder — AMU ZHCET AI Branch
Uses REAL data:
  - 93 students from AI_Results.xlsx (enrollment numbers like GP4453)
  - Names + faculty numbers from students_2023.xlsx
  - Real grades per student per course
  - Real AMU AI curriculum (Semesters 1-8)

Place AI_Results.xlsx in backend/ folder (or project root).
Run:
    python seed_database.py
    python seed_database.py --force   # wipe and re-seed
"""

import sys, os, re
from pathlib import Path

BACKEND_DIR  = Path(__file__).parent
PROJECT_ROOT = BACKEND_DIR.parent
DATA_DIR     = PROJECT_ROOT / "data"

def _find(name):
    for d in [BACKEND_DIR, PROJECT_ROOT, DATA_DIR,
              DATA_DIR / "raw" / "student_source"]:
        p = d / name
        if p.exists():
            return p
    return None

AI_RESULTS_PATH = _find("AI_Results.xlsx")
MASTER_PATH     = _find("students_2023.xlsx.xlsx") or _find("students_2023.xlsx")

sys.path.insert(0, str(BACKEND_DIR))
os.chdir(BACKEND_DIR)

from database import engine, DATABASE_PATH, init_db
from models import Base, Student, Course, AcademicRecord, CourseCategoryEnum, GradeEnum
from sqlalchemy.orm import Session

# ── Real AI Curriculum ───────────────────────────────────────────────────────
# (code, name, category, sem, credits, lec, tut, prac, is_theory, is_lab, is_elective)
COURSES_DATA = [
    # Semester 1 — First Year Common
    ("ACS1112","Applied Chemistry",                         "BS", 1,4,3,1,0,True, False,False),
    ("AMS1122","Applied Mathematics-I",                     "BS", 1,4,3,1,0,True, False,False),
    ("APS1112","Applied Physics",                           "BS", 1,4,3,1,0,True, False,False),
    ("ELA1112","Basic Electrical Engineering",              "ESA",1,4,3,1,0,True, False,False),
    ("MEA1112","Engineering Drawing",                       "ESA",1,2,0,0,4,False,True, False),
    ("MEA1122","Engineering Workshop",                      "ESA",1,2,0,0,4,False,True, False),
    ("CEA1120","Environmental Studies",                     "HM", 1,2,2,0,0,True, False,False),
    # Semester 2 — First Year Common
    ("AMS2630","Applied Mathematics-II",                    "BS", 2,4,3,1,0,True, False,False),
    ("ACS1110","Chemistry Lab",                             "BS", 2,1,0,0,2,False,True, False),
    ("APS1110","Physics Lab",                               "BS", 2,1,0,0,2,False,True, False),
    ("ELA2410","Basic Electronics",                         "ESA",2,4,3,1,0,True, False,False),
    ("MEA1120","Engineering Mechanics",                     "ESA",2,4,3,1,0,True, False,False),
    ("ACO3080","Computer Programming",                      "ESA",2,3,2,0,2,True, False,False),
    # Semester 3 — AI Branch
    ("AIC2022","Introduction to Artificial Intelligence",   "PC", 3,4,3,1,0,True, False,False),
    ("AIC2062","Data Structure and Algorithm",              "PC", 3,4,3,1,0,True, False,False),
    ("AIC2072","Digital Logic and System Design",           "PC", 3,4,3,1,0,True, False,False),
    ("AIC2122","Database Management System",                "PC", 3,4,3,1,0,True, False,False),
    ("AIC2922","Artificial Intelligence Lab",               "PC", 3,2,0,1,2,False,True, False),
    ("AMS2612","Higher Mathematics",                        "BS", 3,4,3,1,0,True, False,False),
    ("ELA2112","Electronic Devices & Circuits",             "ESA",3,4,3,1,0,True, False,False),
    # Semester 4 — AI Branch
    ("AIC2042","Principles of Machine Learning",            "PC", 4,4,3,1,0,True, False,False),
    ("AIC2142","Design & Analysis of Algorithm",            "PC", 4,4,3,1,0,True, False,False),
    ("AIC2152","AI Tools & Techniques",                     "PC", 4,4,3,1,0,True, False,False),
    ("AIC2912","Data Structure Lab",                        "PC", 4,2,0,1,2,False,True, False),
    ("AIP2922","Colloquium",                                "PSI",4,2,0,2,0,False,True, False),
    ("AMS2632","Discrete Structures",                       "BS", 4,4,3,1,0,True, False,False),
    ("ELA2412","Fundamentals of Digital Signal Processing", "ESA",4,4,3,1,0,True, False,False),
    ("ELA2902","Electronics Laboratory",                    "ESA",4,2,0,1,2,False,True, False),
    # Semester 5 — AI Branch
    ("AIC3072","AI System Design",                          "PC", 5,4,3,1,0,True, False,False),
    ("AIC3092","Microprocessor Theory & Applications",      "PC", 5,3,3,0,0,True, False,False),
    ("AIC3102","Operating Systems",                         "PC", 5,4,3,1,0,True, False,False),
    ("AIC3942","Machine Learning Lab",                      "PC", 5,2,0,1,2,False,True, False),
    ("AIP3932","Minor Project-I",                           "PSI",5,2,0,0,4,False,True, False),
    ("ELA3402","Communication Systems",                     "ESA",5,4,3,1,0,True, False,False),
    ("MEH3452","Engineering Economy & Management",          "HM", 5,3,3,0,0,True, False,False),
    ("OE5001", "Open Elective-1",                           "OE", 5,3,3,0,0,True, False,True),
    # Semester 6 — AI Branch
    ("AIC3132","Computer Networks",                         "PC", 6,4,3,1,0,True, False,False),
    ("AIC3142","Deep Learning",                             "PC", 6,4,3,1,0,True, False,False),
    ("AIC3172","Natural Language Processing",               "PC", 6,4,3,1,0,True, False,False),
    ("AIC3972","Deep Learning Lab",                         "PC", 6,2,3,1,0,False,True, False),
    ("AIC3982","Microprocessor & Embedded Systems Lab",     "PC", 6,2,0,1,2,False,True, False),
    ("AIP3952","Minor Project-II",                          "PSI",6,2,0,0,4,False,True, False),
    ("OE6001", "Open Elective-2",                           "OE", 6,3,3,0,0,True, False,True),
    ("HM6001", "Humanities Elective",                       "HM", 6,3,3,0,0,True, False,True),
    # Semester 7 — AI Branch
    ("AIC4252","Advanced Machine Learning",                 "PC", 7,4,3,1,0,True, False,False),
    ("AIC4972","Advanced Artificial Intelligence Lab",      "PC", 7,2,0,1,2,False,True, False),
    ("AIP4982","Project Phase-I",                           "PSI",7,4,0,0,8,False,True, False),
    ("AIE4260","Departmental Elective-1",                   "DE", 7,3,3,0,0,True, False,True),
    ("AIE4370","Departmental Elective-2",                   "DE", 7,3,3,0,0,True, False,True),
    ("AIE4570","Departmental Elective-3",                   "DE", 7,3,3,0,0,True, False,True),
    ("AIC3120","Departmental Elective-4",                   "DE", 7,3,3,0,0,True, False,True),
    # Semester 8 — AI Branch
    ("AIP4802","Industrial Training/Internship",            "PSI",8,2,0,0,0,False,False,False),
    ("AIP4992","Project Phase-II",                          "PSI",8,6,0,0,12,False,True, False),
    ("AIC3130","Departmental Elective-5",                   "DE", 8,3,3,0,0,True, False,True),
    ("AIC3140","Departmental Elective-6",                   "DE", 8,3,3,0,0,True, False,True),
    # Extra course codes seen in results data (older curriculum codes)
    ("AIC2940","AI Techniques (Legacy)",                    "PC", 3,4,3,1,0,True, False,False),
    ("AIC3950","Advanced AI Lab (Legacy)",                  "PC", 5,2,0,1,2,False,True, False),
    ("AIC3970","ML Lab (Legacy)",                           "PC", 5,2,0,1,2,False,True, False),
    ("AIC4980","Project I (Legacy)",                        "PSI",7,4,0,0,8,False,True, False),
    ("AIC4990","Project II (Legacy)",                       "PSI",8,6,0,0,12,False,True,False),
    ("AMO4430","Open Elective Math (Legacy)",               "OE", 7,3,3,0,0,True, False,True),
    ("APO3040","Open Elective Applied (Legacy)",            "OE", 5,3,3,0,0,True, False,True),
    ("CEO4720","Civil Engg Elective (Legacy)",              "OE", 7,3,3,0,0,True, False,True),
    ("COO4470","Computer Elective (Legacy)",                "OE", 7,3,3,0,0,True, False,True),
    ("EEO4210","EE Elective (Legacy)",                      "OE", 5,3,3,0,0,True, False,True),
    ("EZH3010","Elective-Humanities I",                     "HM", 5,3,3,0,0,True, False,True),
    ("EZH3020","Elective-Humanities II",                    "HM", 6,3,3,0,0,True, False,True),
    ("EZH3030","Elective-Humanities III",                   "HM", 7,3,3,0,0,True, False,True),
    ("MEO4220","Mech Elective (Legacy)",                    "OE", 5,3,3,0,0,True, False,True),
    ("AIC2130","AI Foundations (Legacy)",                   "PC", 3,4,3,1,0,True, False,False),
    ("AIC2140","Data Analysis (Legacy)",                    "PC", 3,4,3,1,0,True, False,False),
    ("AIC2150","ML Fundamentals (Legacy)",                  "PC", 3,4,3,1,0,True, False,False),
]

GRADE_POINTS = {"A+":10,"A":9,"B+":8,"B":7,"C":6,"D":5,"E":0,"F":0,"I":0,"Z":0}
PASS_GRADES  = {"A+","A","B+","B","C","D"}

def grade_to_marks(grade, is_theory):
    mapping = {
        "A+":(14,23,55),"A":(13,21,50),"B+":(12,19,45),
        "B":(11,17,40),"C":(10,14,36),"D":(8,11,33),
        "E":(6,8,18),"F":(4,5,10),"I":(0,0,0),
    }
    cw,mid,end = mapping.get(grade,(8,11,33))
    return float(cw), float(mid), float(end)

def parse_grades(s):
    out = {}
    for part in str(s).split(','):
        m = re.match(r'\s*([A-Z]{2,3}\d{4}[A-Z]?)\s*:\s*([A-Z+]+)', part.strip())
        if m:
            out[m.group(1)] = m.group(2)
    return out

def infer_sem_year_np(cum_ec, result_str, master_sem):
    r = str(result_str)
    if 'Graduated' in r:
        return 8, 2020, 0
    np_count = 2 if 'Not Promoted' in r else (1 if r.strip() == 'Fail' else 0)
    next_sem = master_sem + 2  # Excel is Sem 4 results; students are now in Sem 6 (one full academic year later)
    year_map = {2:2023, 4:2022, 6:2021}
    adm_year = year_map.get(master_sem, 2023)
    return next_sem, adm_year, np_count

def main():
    import pandas as pd

    print(f"📦 Seeding database at: {DATABASE_PATH}")
    init_db()

    if not AI_RESULTS_PATH:
        print("❌ AI_Results.xlsx not found. Place it in the backend/ folder.")
        sys.exit(1)

    # Load results
    rdf = pd.read_excel(AI_RESULTS_PATH)
    rdf.columns = ['Sem','Br','EnrolN','Grades',
                   *[f'_{i}' for i in range(4,27)],
                   'SPI','CPI','CumEC','Result']

    # Load master
    if MASTER_PATH:
        mdf = pd.read_excel(MASTER_PATH, header=1)
        mdf.columns = ['F_No','En_No','Name','Hall','Branch','Sem','Mob','Email']
        merged = rdf.merge(mdf[['F_No','En_No','Name','Sem']],
                           left_on='EnrolN', right_on='En_No', how='left')
    else:
        rdf['Name'] = rdf['EnrolN']
        rdf['F_No'] = rdf['EnrolN']
        rdf['Sem_y'] = 2
        merged = rdf

    with Session(engine) as db:
        if db.query(Student).count() > 0:
            print("⚠️  Already seeded. Use --force to wipe and re-seed.")
            if "--force" not in sys.argv:
                return
            print("🗑️  Wiping data...")
            db.query(AcademicRecord).delete()
            db.query(Student).delete()
            db.query(Course).delete()
            db.commit()

        # Insert courses
        print("📚 Inserting real AMU AI curriculum...")
        cat_map = {e.value: e for e in CourseCategoryEnum}
        course_map = {}  # code → ORM obj

        for code,name,cat,sem,cred,lec,tut,prac,theory,lab,elective in COURSES_DATA:
            c = Course(
                course_code=code, course_name=name,
                category=cat_map[cat], branch="AI",
                semester=sem, credits=cred,
                lecture_hours=lec, tutorial_hours=tut, practical_hours=prac,
                is_theory=theory, is_lab=lab, is_elective=elective,
                coursework_marks=15 if theory else 60,
                midsem_marks=25 if theory else 40,
                endsem_marks=60 if theory else 0,
            )
            db.add(c)
            course_map[code] = c

        db.flush()
        print(f"   ✅ {len(course_map)} courses inserted")

        # Insert students + records
        print("👥 Inserting 93 real AI students with grades...")
        students_added = records_added = 0
        samples = []

        for _, row in merged.iterrows():
            enrol  = str(row['EnrolN']).strip()
            fac    = str(row.get('F_No', enrol)).strip()
            name   = str(row.get('Name', enrol)).strip()
            cpi    = float(row['CPI'])  if pd.notna(row['CPI'])  else 0.0
            spi    = float(row['SPI'])  if pd.notna(row['SPI'])  else 0.0
            cum_ec = int(row['CumEC'])  if pd.notna(row['CumEC']) else 0
            result = str(row['Result']).strip()
            grades = str(row['Grades'])
            msem   = int(row.get('Sem_y', 2)) if pd.notna(row.get('Sem_y', 2)) else 2

            cur_sem, adm_yr, np_cnt = infer_sem_year_np(cum_ec, result, msem)

            s = Student(
                faculty_number=fac, enrollment_number=enrol, name=name,
                branch="AI", current_semester=cur_sem, admission_year=adm_yr,
                cgpa=round(cpi,3), sgpa=round(spi,3),
                total_earned_credits=cum_ec, not_promoted_count=np_cnt,
            )
            db.add(s)
            db.flush()
            students_added += 1
            if len(samples) < 5:
                samples.append((s.id, fac, enrol, name, cur_sem, cpi))

            # Academic records from grade string
            grade_map = parse_grades(grades)
            exam_sem = msem  # grades are from this semester

            for code, grade in grade_map.items():
                c_obj = course_map.get(code)
                if not c_obj:
                    continue
                cw, mid, end = grade_to_marks(grade, c_obj.is_theory)
                valid_grade  = grade if grade in GRADE_POINTS else "I"
                rec = AcademicRecord(
                    student_id=s.id, course_id=c_obj.id,
                    semester=exam_sem, attempt_number=1,
                    coursework_obtained=cw, midsem_obtained=mid,
                    endsem_obtained=end, total_marks=cw+mid+end,
                    grade=GradeEnum(valid_grade),
                    grade_points=float(GRADE_POINTS.get(valid_grade, 0)),
                    status="PASSED" if grade in PASS_GRADES else "FAILED",
                    attendance_fulfilled=(grade not in ("F","I")),
                    attendance_percentage=75.0 if grade not in ("F","I") else 50.0,
                )
                db.add(rec)
                records_added += 1

        db.commit()

    print(f"   ✅ {students_added} students inserted")
    print(f"   ✅ {records_added} academic records inserted")
    print("\n   Sample student IDs:")
    for sid, fno, eno, sname, csem, cgpa in samples:
        print(f"   id={sid}  faculty={fno}  enrol={eno}  name={sname}  sem={csem}  cgpa={cgpa:.3f}")
    print("\n🎉 Done! Login with faculty_number + enrollment_number (e.g. 23AIBEA203 / GP4453)")

if __name__ == "__main__":
    main()
