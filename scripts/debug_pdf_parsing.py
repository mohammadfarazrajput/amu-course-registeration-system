
import pdfplumber
from pathlib import Path

PDF_PATH = Path('d:/deep_learning/courseRegisteration/college-course-registration-automation-system/data/raw/curriculum/PK_effective_from_2023.pdf')

def debug_pdf():
    print(f"Opening {PDF_PATH}")
    if not PDF_PATH.exists():
        print("File not found!")
        return

    with pdfplumber.open(PDF_PATH) as pdf:
        # Check first few pages
        for i, page in enumerate(pdf.pages[:3]):
            print(f"\n--- Page {i+1} ---")
            text = page.extract_text()
            print("TEXT EXTRACT (first 200 chars):")
            print(text[:200] if text else "No text found")
            
            tables = page.extract_tables()
            print(f"Found {len(tables)} tables")
            
            for j, table in enumerate(tables):
                print(f"Table {j+1} (first 3 rows):")
                for row in table[:3]:
                    print(row)

if __name__ == "__main__":
    debug_pdf()
