"""
Data Validation and Sanitization Engine.
Provides strict validation rules and type coercion for student, course,
and grade records, preventing corrupt data and injection vectors.
"""

import re
from datetime import datetime, date
from typing import Optional, Tuple, Union
import config


class ValidationError(ValueError):
    """Raised when an input field fails business logic or format validation."""
    pass


def validate_name(name: str, field_name: str = "Name") -> str:
    """Validates that a name contains valid characters and length."""
    if not isinstance(name, str):
        raise ValidationError(f"{field_name} must be a string.")
    cleaned = name.strip()
    if not cleaned:
        raise ValidationError(f"{field_name} cannot be empty.")
    if len(cleaned) < 2 or len(cleaned) > 50:
        raise ValidationError(f"{field_name} must be between 2 and 50 characters.")
    # Allow alphabetic characters, spaces, hyphens, and apostrophes
    if not re.match(r"^[A-Za-zÀ-ÖØ-öø-ÿ\s\-']+$", cleaned):
        raise ValidationError(f"{field_name} contains invalid characters.")
    return cleaned


def validate_student_code(code: str) -> str:
    """Validates student identifier code (e.g., STU-1001, S12345)."""
    if not isinstance(code, str):
        raise ValidationError("Student Code must be a string.")
    cleaned = code.strip().upper()
    if not cleaned:
        raise ValidationError("Student Code cannot be empty.")
    if not re.match(r"^[A-Z0-9_\-]{3,20}$", cleaned):
        raise ValidationError("Student Code must be 3-20 alphanumeric characters (hyphens/underscores allowed).")
    return cleaned


def validate_email(email: str) -> str:
    """Validates email format strictly against standard email pattern."""
    if not isinstance(email, str):
        raise ValidationError("Email must be a string.")
    cleaned = email.strip().lower()
    if not cleaned:
        raise ValidationError("Email cannot be empty.")
    email_regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    if not re.match(email_regex, cleaned) or len(cleaned) > 100:
        raise ValidationError(f"Invalid email address format: '{email}'.")
    return cleaned


def validate_phone(phone: Optional[str]) -> Optional[str]:
    """Validates optional contact phone number."""
    if not phone or not phone.strip():
        return None
    cleaned = phone.strip()
    # Permit standard international and domestic formats
    if not re.match(r"^\+?[0-9\s\-().]{7,25}$", cleaned):
        raise ValidationError(f"Invalid phone number format: '{phone}'.")
    return cleaned


def validate_date(date_str: str, field_name: str = "Date") -> str:
    """Validates and standardizes a date string in YYYY-MM-DD format."""
    if not isinstance(date_str, str):
        raise ValidationError(f"{field_name} must be a string.")
    cleaned = date_str.strip()
    try:
        parsed = datetime.strptime(cleaned, "%Y-%m-%d").date()
        return parsed.strftime("%Y-%m-%d")
    except ValueError:
        raise ValidationError(f"{field_name} must follow YYYY-MM-DD format (e.g. 2005-09-15).")


def validate_dob(dob_str: str) -> str:
    """Validates student Date of Birth, verifying age is between 12 and 100."""
    standard_dob = validate_date(dob_str, "Date of Birth")
    dob_date = datetime.strptime(standard_dob, "%Y-%m-%d").date()
    today = date.today()

    if dob_date >= today:
        raise ValidationError("Date of birth must be in the past.")

    # Calculate approximate age
    age = today.year - dob_date.year - ((today.month, today.day) < (dob_date.month, dob_date.day))
    if age < 12:
        raise ValidationError(f"Student age ({age} years) is below minimum admission age (12).")
    if age > 100:
        raise ValidationError(f"Student age ({age} years) exceeds realistic limit.")
    return standard_dob


def validate_enrollment_date(enroll_date_str: str, dob_str: Optional[str] = None) -> str:
    """Validates enrollment date and ensures it is after DOB."""
    standard_date = validate_date(enroll_date_str, "Enrollment Date")
    if dob_str:
        dob_date = datetime.strptime(validate_date(dob_str), "%Y-%m-%d").date()
        enroll_date = datetime.strptime(standard_date, "%Y-%m-%d").date()
        if enroll_date <= dob_date:
            raise ValidationError("Enrollment date must occur after Date of Birth.")
    return standard_date


def validate_student_status(status: str) -> str:
    """Validates student academic standing."""
    valid_statuses = ("Active", "Suspended", "Graduated", "Withdrawn")
    cleaned = status.strip().capitalize()
    if cleaned not in valid_statuses:
        raise ValidationError(f"Invalid status '{status}'. Must be one of: {', '.join(valid_statuses)}.")
    return cleaned


def validate_course_code(code: str) -> str:
    """Validates course identification code (e.g. CS101, MATH-201)."""
    if not isinstance(code, str):
        raise ValidationError("Course Code must be a string.")
    cleaned = code.strip().upper()
    if not cleaned:
        raise ValidationError("Course Code cannot be empty.")
    if not re.match(r"^[A-Z0-9_\-]{2,15}$", cleaned):
        raise ValidationError("Course Code must be 2-15 alphanumeric characters (e.g., CS101, PHYS-202).")
    return cleaned


def validate_course_name(name: str) -> str:
    """Validates course title."""
    if not isinstance(name, str):
        raise ValidationError("Course Name must be a string.")
    cleaned = name.strip()
    if len(cleaned) < 3 or len(cleaned) > 100:
        raise ValidationError("Course Name must be between 3 and 100 characters.")
    return cleaned


def validate_credits(credits_val: Union[int, str]) -> int:
    """Validates academic credit unit hours (1 to 6)."""
    try:
        val = int(credits_val)
    except (ValueError, TypeError):
        raise ValidationError(f"Credits must be an integer, got '{credits_val}'.")
    if val < 1 or val > 6:
        raise ValidationError("Credits must be between 1 and 6.")
    return val


def validate_capacity(cap_val: Union[int, str]) -> int:
    """Validates course maximum student capacity."""
    try:
        val = int(cap_val)
    except (ValueError, TypeError):
        raise ValidationError(f"Capacity must be an integer, got '{cap_val}'.")
    if val < 1 or val > 500:
        raise ValidationError("Course capacity must be between 1 and 500 students.")
    return val


def validate_semester(sem_str: str) -> str:
    """Validates academic semester string (e.g. 'Fall 2026', 'Spring 2026')."""
    if not isinstance(sem_str, str):
        raise ValidationError("Semester must be a string.")
    cleaned = sem_str.strip()
    if not cleaned:
        raise ValidationError("Semester cannot be empty.")
    # Check common format: Term Year
    if not re.match(r"^(Fall|Spring|Summer|Winter)\s+20\d{2}$", cleaned, re.IGNORECASE):
        # Relax slightly if custom semester string is given
        if len(cleaned) < 3 or len(cleaned) > 30:
            raise ValidationError("Semester must be 3-30 characters (e.g. 'Fall 2026').")
    return cleaned.title()


def score_to_letter_grade(score: float) -> Tuple[str, float]:
    """
    Maps a percentage score (0-100) to corresponding letter grade and GPA points.
    Returns (letter_grade, grade_point).
    """
    for grade, data in config.GRADE_SCALE.items():
        if score >= data["min_score"]:
            return grade, data["points"]
    return "F", 0.0


def validate_score(score_val: Union[float, int, str, None]) -> Optional[float]:
    """Validates an academic grade score between 0.0 and 100.0."""
    if score_val is None or (isinstance(score_val, str) and score_val.strip() == ""):
        return None
    try:
        val = float(score_val)
    except (ValueError, TypeError):
        raise ValidationError(f"Numeric score must be a number, got '{score_val}'.")
    if val < 0.0 or val > 100.0:
        raise ValidationError(f"Score must be between 0.0 and 100.0, got {val}.")
    return round(val, 2)


def validate_letter_grade(grade_str: Optional[str]) -> Optional[str]:
    """Validates standard letter grades."""
    if not grade_str or not grade_str.strip():
        return None
    cleaned = grade_str.strip().upper()
    valid_grades = set(config.GRADE_SCALE.keys()) | {"W", "I"}
    if cleaned not in valid_grades:
        raise ValidationError(f"Invalid letter grade '{grade_str}'. Valid: {', '.join(sorted(valid_grades))}.")
    return cleaned


def letter_grade_to_points(grade_str: str) -> Optional[float]:
    """Returns grade points on 4.0 scale for letter grade."""
    cleaned = grade_str.strip().upper()
    if cleaned in config.GRADE_SCALE:
        return config.GRADE_SCALE[cleaned]["points"]
    return None
