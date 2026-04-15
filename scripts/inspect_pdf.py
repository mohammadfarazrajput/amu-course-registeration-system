
import pdfplumber
from pathlib import Path

# Path to a sample curriculum PDF
pdf_path = Path("data/raw/curriculum/AI_effective_from_2023.pdf")

if not pdf_path.exists():
    print(f"File not found: {pdf_path}")
    # Try finding any pdf in the dir
    pdf_dir = Path("data/raw/curriculum")
    pdfs = list(pdf_dir.glob("*.pdf"))
    if pdfs:
        pdf_path = pdfs[0]
        print(f"Using {pdf_path} instead.")
    else:
        print("No PDFs found.")
        exit()

print(f"Inspecting: {pdf_path}")

with pdfplumber.open(pdf_path) as pdf:
    for i, page in enumerate(pdf.pages[:3]): # Check first 3 pages
        print(f"\n--- Page {i+1} ---")
        
        # 1. extract text
        text = page.extract_text()
        print("Text Preview (first 200 chars):")
        print(text[:200] if text else "No text found")
        
        # 2. extract tables
        tables = page.extract_tables()
        print(f"\nFound {len(tables)} tables")
        
        for j, table in enumerate(tables):
            print(f"\nTable {j+1} (first 3 rows):")
            for row in table[:3]:
                print(row)
