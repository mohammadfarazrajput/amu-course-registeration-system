import pandas as pd


class StudentExtractor:

    def __init__(self, excel_path: str):
        self.excel_path = excel_path

    def extract_students(self):
        df = pd.read_excel(self.excel_path)

        students = []

        for _, row in df.iterrows():
            students.append({
                "name": row.get("Name"),
                "faculty_no": row.get("Faculty No"),
                "enrollment_no": row.get("Enrollment No"),
                "branch": row.get("Branch"),
                "admission_year": row.get("Admission Year"),
            })

        return students
