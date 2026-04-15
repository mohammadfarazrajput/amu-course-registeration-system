from sqlalchemy.orm import Session
import backend.models as models


class DBLoader:

    @staticmethod
    def load_courses(db: Session, records):
        for r in records:
            course = models.Course(
                branch=r["branch"],
                course_code=r["course_code"],
                credits=r["credits"],
                semester=r.get("year_level")
            )
            db.add(course)

        db.commit()
