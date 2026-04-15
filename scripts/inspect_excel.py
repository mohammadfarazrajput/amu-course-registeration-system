
import pandas as pd
from pathlib import Path

file_path = Path("data/raw/student_source/students_2023.xlsx.xlsx")

try:
    df = pd.read_excel(file_path, header=None, nrows=15)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_colwidth', None)
    
    for idx, row in df.iterrows():
        print(f"Row {idx}: {row.values.tolist()}")
except Exception as e:
    print(f"Error reading Excel: {e}")
