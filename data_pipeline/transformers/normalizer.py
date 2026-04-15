class Normalizer:

    @staticmethod
    def add_semester_from_code(records):
        for r in records:
            code = r["course_code"]
            if len(code) >= 4 and code[3].isdigit():
                r["year_level"] = int(code[3])
            else:
                r["year_level"] = None

        return records
