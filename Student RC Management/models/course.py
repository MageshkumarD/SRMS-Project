"""
Course Domain Model.
Represents an academic course with credit unit and capacity controls.
"""

from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any
from utils.validators import (
    validate_course_code,
    validate_course_name,
    validate_credits,
    validate_capacity,
)


@dataclass
class Course:
    course_code: str
    course_name: str
    credits: int
    description: Optional[str] = None
    dept_code: Optional[str] = None
    max_capacity: int = 40
    course_id: Optional[int] = None
    created_at: Optional[str] = None

    def __post_init__(self):
        """Sanitize and validate course parameters."""
        self.course_code = validate_course_code(self.course_code)
        self.course_name = validate_course_name(self.course_name)
        self.credits = validate_credits(self.credits)
        self.max_capacity = validate_capacity(self.max_capacity)
        if self.description:
            self.description = self.description.strip()
        if self.dept_code:
            self.dept_code = self.dept_code.strip().upper()

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_row(cls, row: Dict[str, Any]) -> "Course":
        """Instantiates a Course model directly from a database row dictionary."""
        return cls(
            course_id=row.get("course_id"),
            course_code=row["course_code"],
            course_name=row["course_name"],
            description=row.get("description"),
            credits=int(row["credits"]),
            dept_code=row.get("dept_code"),
            max_capacity=int(row.get("max_capacity", 40)),
            created_at=str(row.get("created_at")) if row.get("created_at") else None,
        )
