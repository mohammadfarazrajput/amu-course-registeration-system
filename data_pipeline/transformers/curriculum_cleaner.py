class CurriculumCleaner:

    @staticmethod
    def clean(records):
        cleaned = []

        for r in records:
            if not r["course_code"]:
                continue

            credits = r["credits"]
            try:
                credits = int(float(credits))
            except:
                credits = 0

            cleaned.append({
                "branch": r["branch"],
                "course_code": str(r["course_code"]).strip(),
                "course_title": str(r["course_title"]).strip(),
                "credits": credits
            })

        return cleaned
