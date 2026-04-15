"""
Document Processing Service
Handles PDF parsing, table extraction, and OCR
"""

import pdfplumber
import pytesseract
from PIL import Image
from pathlib import Path
from typing import Dict, List
import pandas as pd
import re


class DocumentProcessor:
    """Process uploaded documents (PDFs, images)"""
    
    def __init__(self):
        self.supported_formats = ['.pdf', '.jpg', '.jpeg', '.png']
    
    def process_document(self, file_path: str) -> Dict:
        """
        Process a document and extract structured data
        
        Returns:
            Dict with extracted text, tables, and metadata
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Determine processing method
        if file_path.suffix.lower() == '.pdf':
            return self._process_pdf(file_path)
        elif file_path.suffix.lower() in ['.jpg', '.jpeg', '.png']:
            return self._process_image(file_path)
        else:
            raise ValueError(f"Unsupported format: {file_path.suffix}")
    
    def _process_pdf(self, pdf_path: Path) -> Dict:
        """Process PDF file"""
        result = {
            "text": "",
            "tables": [],
            "metadata": {},
            "is_structured": False
        }
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                # Extract text
                text_parts = []
                for page in pdf.pages:
                    text_parts.append(page.extract_text() or "")
                result["text"] = "\n\n".join(text_parts)
                
                # Extract tables
                for i, page in enumerate(pdf.pages):
                    tables = page.extract_tables()
                    for table in tables:
                        if table:
                            result["tables"].append({
                                "page": i + 1,
                                "data": table
                            })
                
                # Metadata
                result["metadata"] = {
                    "pages": len(pdf.pages),
                    "has_tables": len(result["tables"]) > 0,
                    "source": pdf_path.name
                }
                
                # Check if structured (has tables)
                result["is_structured"] = len(result["tables"]) > 0
        
        except Exception as e:
            print(f"Error processing PDF: {e}")
            result["error"] = str(e)
        
        return result
    
    def _process_image(self, image_path: Path) -> Dict:
        """Process image using OCR"""
        result = {
            "text": "",
            "tables": [],
            "metadata": {},
            "is_structured": False
        }
        
        try:
            # OCR
            image = Image.open(image_path)
            text = pytesseract.image_to_string(image)
            result["text"] = text
            
            # Metadata
            result["metadata"] = {
                "source": image_path.name,
                "ocr": True
            }
            
            # Try to detect tables in text
            result["is_structured"] = self._detect_tabular_data(text)
        
        except Exception as e:
            print(f"Error processing image: {e}")
            result["error"] = str(e)
        
        return result
    
    def _detect_tabular_data(self, text: str) -> bool:
        """Detect if text contains tabular data (marks, credits, etc.)"""
        indicators = [
            r'marks|grade|credits|semester|cgpa|sgpa',
            r'\d+\.\d+|\d+/\d+',  # Scores like 85.5 or 85/100
            r'[A-Z]\+?',  # Grades like A, B+
        ]
        
        matches = sum(1 for pattern in indicators if re.search(pattern, text, re.IGNORECASE))
        return matches >= 2
    
    def extract_marksheet_data(self, file_path: str) -> Dict:
        """
        Extract structured academic data from marksheet
        
        Returns:
            Dict with courses, marks, grades, semester info
        """
        doc_data = self.process_document(file_path)
        
        extracted = {
            "student_id": None,
            "semester": None,
            "courses": [],
            "cgpa": None,
            "sgpa": None,
            "is_marksheet": False
        }
        
        text = doc_data.get("text", "")
        
        # Extract student ID patterns
        student_id_match = re.search(r'(?:Enrollment|Faculty|Roll)\s*(?:No|Number)?[:\s]+(\d+)', text, re.IGNORECASE)
        if student_id_match:
            extracted["student_id"] = student_id_match.group(1)
        
        # Extract semester
        sem_match = re.search(r'Semester[:\s]+(\d+)', text, re.IGNORECASE)
        if sem_match:
            extracted["semester"] = int(sem_match.group(1))
        
        # Extract CGPA/SGPA
        cgpa_match = re.search(r'CGPA[:\s]+([\d.]+)', text, re.IGNORECASE)
        if cgpa_match:
            extracted["cgpa"] = float(cgpa_match.group(1))
        
        sgpa_match = re.search(r'SGPA[:\s]+([\d.]+)', text, re.IGNORECASE)
        if sgpa_match:
            extracted["sgpa"] = float(sgpa_match.group(1))
        
        # Extract course data from tables
        if doc_data.get("tables"):
            for table_info in doc_data["tables"]:
                table = table_info["data"]
                courses = self._parse_course_table(table)
                extracted["courses"].extend(courses)
        
        # Determine if this is a marksheet
        extracted["is_marksheet"] = (
            extracted["student_id"] is not None or
            extracted["semester"] is not None or
            len(extracted["courses"]) > 0
        )
        
        return extracted
    
    def _parse_course_table(self, table: List[List]) -> List[Dict]:
        """Parse course information from table"""
        courses = []
        
        if not table or len(table) < 2:
            return courses
        
        # Try to find header row
        header = table[0]
        
        # Look for common column patterns
        for row in table[1:]:
            if len(row) < 3:
                continue
            
            course_info = {
                "course_code": None,
                "course_name": None,
                "credits": None,
                "marks": None,
                "grade": None
            }
            
            # Simple heuristic parsing
            for i, cell in enumerate(row):
                if not cell:
                    continue
                
                cell = str(cell).strip()
                
                # Course code pattern (e.g., AIC2022)
                if re.match(r'^[A-Z]{2,3}[A-Z0-9]{4,5}$', cell):
                    course_info["course_code"] = cell
                
                # Grade pattern
                elif re.match(r'^[A-Z]\+?$', cell):
                    course_info["grade"] = cell
                
                # Credits (single digit)
                elif re.match(r'^\d$', cell):
                    course_info["credits"] = int(cell)
                
                # Marks pattern
                elif re.match(r'^\d{1,3}$', cell):
                    marks_val = int(cell)
                    if 0 <= marks_val <= 100:
                        course_info["marks"] = marks_val
            
            # Add if we found at least course code or grade
            if course_info["course_code"] or course_info["grade"]:
                courses.append(course_info)
        
        return courses
    
    def chunk_document(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """
        Chunk document text for vector storage
        
        Args:
            text: Document text
            chunk_size: Target chunk size in characters
            overlap: Overlap between chunks
        
        Returns:
            List of text chunks
        """
        if not text:
            return []
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            
            # Try to break at sentence boundary
            if end < len(text):
                last_period = chunk.rfind('.')
                if last_period > chunk_size // 2:
                    end = start + last_period + 1
                    chunk = text[start:end]
            
            chunks.append(chunk.strip())
            start = end - overlap
        
        return chunks


# Singleton instance
document_processor = DocumentProcessor()