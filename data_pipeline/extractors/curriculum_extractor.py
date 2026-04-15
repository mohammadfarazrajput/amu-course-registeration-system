import os
import pdfplumber
import pandas as pd


class CurriculumExtractor:

    def __init__(self, raw_folder: str):
        self.raw_folder = raw_folder

    def extract_all(self):
        extracted_data = []

        for root, _, files in os.walk(self.raw_folder):
            for file in files:
                if file.endswith(".pdf"):
                    pdf_path = os.path.join(root, file)
                    branch = os.path.basename(root)
                    data = self._extract_single(pdf_path, branch)
                    extracted_data.extend(data)

        return extracted_data

    def _extract_single(self, pdf_path: str, branch: str):
        records = []

        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()

                for table in tables:
                    df = pd.DataFrame(table[1:], columns=table[0])

                    for _, row in df.iterrows():
                        if "Course No." in df.columns:
                            course_code = row.get("Course No.")
                        elif "Course" in df.columns:
                            course_code = row.get("Course")
                        else:
                            continue

                        records.append({
                            "branch": branch,
                            "course_code": course_code,
                            "course_title": row.get("Course title", ""),
                            "credits": row.get("Credits", ""),
                            "raw_row": dict(row)
                        })

        return records
