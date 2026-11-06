"""
Enrollment & Grade Domain Model.
Binds a student to a course per semester and maintains academic performance metrics.
"""

from dataclasses import dataclass, asdict
from datetime import date
from typing import Optional, Dict, Any
from utils.validators import (
    validate_semester,
    validate_score,
    validate_letter_grade,
    score_to_letter_grade,
    letter_grade_to_points,
    validate_date,
    ValidationError,
)


@dataclass
class Enrollment:
    student_id: int
    course_id: int
    semester: str
    enrollment_date: str
    numeric_score: Optional[float] = None
    letter_grade: Optional[str] = None
    grade_point: Optional[float] = None
    status: str = "Enrolled"
    grade_date: Optional[str] = None
    enrollment_id: Optional[int] = None

    def __post_init__(self):
        """Validates enrollment fields and synchronizes score and letter grade."""
        self.semester = validate_semester(self.semester)
        self.enrollment_date = validate_date(self.enrollment_date, "Enrollment Date")

        valid_statuses = ("Enrolled", "Completed", "Dropped")
        clean_status = self.status.strip().capitalize()
        if clean_status not in valid_statuses:
            raise ValidationError(f"Invalid enrollment status '{self.status}'. Valid: {', '.join(valid_statuses)}")
        self.status = clean_status

        if self.numeric_score is not None:
            self.numeric_score = validate_score(self.numeric_score)
            calc_grade, calc_points = score_to_letter_grade(self.numeric_score)
            self.letter_grade = self.letter_grade or calc_grade
            self.grade_point = self.grade_point if self.grade_point is not None else calc_points
            if self.status == "Enrolled":
                self.status = "Completed"
            if not self.grade_date:
                self.grade_date = date.today().strftime("%Y-%m-%d")
        elif self.letter_grade is not None:
            self.letter_grade = validate_letter_grade(self.letter_grade)
            self.grade_point = letter_grade_to_points(self.letter_grade)

    def assign_grade(self, score: float) -> None:
        """Assigns numeric score and automatically computes corresponding letter grade and GPA points."""
        validated = validate_score(score)
        self.numeric_score = validated
        grade, points = score_to_letter_grade(validated)
        self.letter_grade = grade
        self.grade_point = points
        self.status = "Completed"
        self.grade_date = date.today().strftime("%Y-%m-%d")

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_row(cls, row: Dict[str, Any]) -> "Enrollment":
        """Instantiates an Enrollment model directly from a database row dictionary."""
        return cls(
            enrollment_id=row.get("enrollment_id"),
            student_id=int(row["student_id"]),
            course_id=int(row["course_id"]),
            semester=row["semester"],
            numeric_score=float(row["numeric_score"]) if row.get("numeric_score") is not None else None,
            letter_grade=row.get("letter_grade"),
            grade_point=float(row["grade_point"]) if row.get("grade_point") is not None else None,
            status=row.get("status", "Enrolled"),
            enrollment_date=str(row["enrollment_date"]),
            grade_date=str(row.get("grade_date")) if row.get("grade_date") else None,
        )
