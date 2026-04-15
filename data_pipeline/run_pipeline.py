import os

from extractors.curriculum_extractor import CurriculumExtractor
from transformers.curriculum_cleaner import CurriculumCleaner
from transformers.normalizer import Normalizer
from loaders.json_writer import JSONWriter
from loaders.csv_writer import CSVWriter

RAW_PATH = os.path.join("data", "raw", "curriculum")
PROCESSED_PATH = os.path.join("data", "processed")

def run():
    extractor = CurriculumExtractor(RAW_PATH)
    raw_data = extractor.extract_all()

    cleaned = CurriculumCleaner.clean(raw_data)
    normalized = Normalizer.add_semester_from_code(cleaned)

    JSONWriter.write(
        normalized,
        os.path.join(PROCESSED_PATH, "courses.json")
    )

    CSVWriter.write(
        normalized,
        os.path.join(PROCESSED_PATH, "courses.csv")
    )

    print("Pipeline completed successfully.")

if __name__ == "__main__":
    run()
