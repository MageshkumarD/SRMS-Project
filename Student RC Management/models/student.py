"""
Student Domain Model.
Represents a student entity with data validation and serialization methods.
"""

from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any
from utils.validators import (
    validate_student_code,
    validate_name,
    validate_email,
    validate_phone,
    validate_dob,
    validate_enrollment_date,
    validate_student_status,
)


@dataclass
class Student:
    student_code: str
    first_name: str
    last_name: str
    email: str
    date_of_birth: str
    enrollment_date: str
    phone: Optional[str] = None
    status: str = "Active"
    student_id: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def __post_init__(self):
        """Sanitize and validate student attributes on initialization."""
        self.student_code = validate_student_code(self.student_code)
        self.first_name = validate_name(self.first_name, "First Name")
        self.last_name = validate_name(self.last_name, "Last Name")
        self.email = validate_email(self.email)
        self.phone = validate_phone(self.phone)
        self.date_of_birth = validate_dob(self.date_of_birth)
        self.enrollment_date = validate_enrollment_date(self.enrollment_date, self.date_of_birth)
        self.status = validate_student_status(self.status)

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_row(cls, row: Dict[str, Any]) -> "Student":
        """Instantiates a Student model directly from a database row dictionary."""
        return cls(
            student_id=row.get("student_id"),
            student_code=row["student_code"],
            first_name=row["first_name"],
            last_name=row["last_name"],
            email=row["email"],
            phone=row.get("phone"),
            date_of_birth=str(row["date_of_birth"]),
            enrollment_date=str(row["enrollment_date"]),
            status=row.get("status", "Active"),
            created_at=str(row.get("created_at")) if row.get("created_at") else None,
            updated_at=str(row.get("updated_at")) if row.get("updated_at") else None,
        )
