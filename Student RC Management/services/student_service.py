"""
Student Service Layer.
Encapsulates all Student business logic and CRUD operations with parameterized queries.
"""

from typing import Any, Dict, List, Optional
from database.connection import db, DatabaseManager
from models.student import Student
from utils.validators import (
    ValidationError,
    validate_name,
    validate_email,
    validate_phone,
    validate_student_status,
)


class StudentService:
    def __init__(self, db_manager: DatabaseManager = db):
        self.db = db_manager

    def create_student(self, student: Student) -> int:
        """
        Inserts a new student record into the database.
        Returns the created student's database ID.
        """
        # Ensure student_code and email are unique
        existing_code = self.get_by_code(student.student_code)
        if existing_code:
            raise ValidationError(f"Student code '{student.student_code}' already exists.")

        existing_email = self.get_by_email(student.email)
        if existing_email:
            raise ValidationError(f"Email '{student.email}' is already registered.")

        query = """
            INSERT INTO students (
                student_code, first_name, last_name, email,
                phone, date_of_birth, enrollment_date, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            student.student_code,
            student.first_name,
            student.last_name,
            student.email,
            student.phone,
            student.date_of_birth,
            student.enrollment_date,
            student.status,
        )
        return self.db.execute(query, params)

    def get_by_id(self, student_id: int) -> Optional[Student]:
        """Fetches a student by primary key ID."""
        query = "SELECT * FROM students WHERE student_id = ?"
        row = self.db.fetch_one(query, (student_id,))
        return Student.from_row(row) if row else None

    def get_by_code(self, student_code: str) -> Optional[Student]:
        """Fetches a student by unique student code."""
        query = "SELECT * FROM students WHERE student_code = ?"
        row = self.db.fetch_one(query, (student_code.strip().upper(),))
        return Student.from_row(row) if row else None

    def get_by_email(self, email: str) -> Optional[Student]:
        """Fetches a student by email address."""
        query = "SELECT * FROM students WHERE LOWER(email) = LOWER(?)"
        row = self.db.fetch_one(query, (email.strip(),))
        return Student.from_row(row) if row else None

    def list_all(self, status: Optional[str] = None, limit: int = 100, offset: int = 0) -> List[Student]:
        """Lists students with optional status filter and pagination."""
        if status:
            query = "SELECT * FROM students WHERE status = ? ORDER BY student_id ASC LIMIT ? OFFSET ?"
            rows = self.db.fetch_all(query, (status, limit, offset))
        else:
            query = "SELECT * FROM students ORDER BY student_id ASC LIMIT ? OFFSET ?"
            rows = self.db.fetch_all(query, (limit, offset))
        return [Student.from_row(r) for r in rows]

    def search(self, search_term: str) -> List[Student]:
        """
        Searches students matching query against code, name, or email.
        Fully protected via parameterized wildcards.
        """
        cleaned = search_term.strip()
        pattern = f"%{cleaned}%"
        query = """
            SELECT * FROM students
            WHERE student_code LIKE ?
               OR first_name LIKE ?
               OR last_name LIKE ?
               OR email LIKE ?
            ORDER BY last_name, first_name
        """
        rows = self.db.fetch_all(query, (pattern, pattern, pattern, pattern))
        return [Student.from_row(r) for r in rows]

    def update_student(self, student_id: int, updates: Dict[str, Any]) -> bool:
        """
        Updates designated fields of an existing student.
        Validates values before applying updates.
        """
        student = self.get_by_id(student_id)
        if not student:
            raise ValidationError(f"Student with ID {student_id} not found.")

        valid_fields = {
            "first_name": lambda v: validate_name(v, "First Name"),
            "last_name": lambda v: validate_name(v, "Last Name"),
            "email": validate_email,
            "phone": validate_phone,
            "status": validate_student_status,
        }

        clauses = []
        params = []

        for field, value in updates.items():
            if field in valid_fields and value is not None:
                cleaned_val = valid_fields[field](value)
                # Check email uniqueness if email updated
                if field == "email" and cleaned_val.lower() != student.email.lower():
                    existing = self.get_by_email(cleaned_val)
                    if existing and existing.student_id != student_id:
                        raise ValidationError(f"Email '{cleaned_val}' is already registered to another student.")
                clauses.append(f"{field} = ?")
                params.append(cleaned_val)

        if not clauses:
            return False

        params.append(student_id)
        query = f"UPDATE students SET {', '.join(clauses)} WHERE student_id = ?"
        self.db.execute(query, tuple(params))
        return True

    def delete_student(self, student_id: int) -> bool:
        """
        Deletes a student record by ID.
        Associated enrollments and grades are removed via CASCADE.
        """
        student = self.get_by_id(student_id)
        if not student:
            raise ValidationError(f"Student with ID {student_id} does not exist.")
        query = "DELETE FROM students WHERE student_id = ?"
        self.db.execute(query, (student_id,))
        return True

    def get_transcript(self, student_id: int) -> Dict[str, Any]:
        """
        Generates comprehensive transcript data: student information,
        courses taken, letter grades, credit hours, and calculated cumulative GPA.
        """
        student = self.get_by_id(student_id)
        if not student:
            raise ValidationError(f"Student with ID {student_id} not found.")

        query = """
            SELECT
                e.enrollment_id,
                e.semester,
                c.course_code,
                c.course_name,
                c.credits,
                e.numeric_score,
                e.letter_grade,
                e.grade_point,
                e.status,
                e.grade_date
            FROM enrollments e
            JOIN courses c ON e.course_id = c.course_id
            WHERE e.student_id = ?
            ORDER BY e.semester DESC, c.course_code ASC
        """
        rows = self.db.fetch_all(query, (student_id,))

        total_credits_attempted = 0
        total_credits_earned = 0
        quality_points = 0.0
        gpa_credits = 0

        for r in rows:
            credits = int(r["credits"])
            total_credits_attempted += credits
            if r["letter_grade"] and r["letter_grade"] not in ("F", "W", "I"):
                total_credits_earned += credits

            # Quality points for GPA calculation
            if r["grade_point"] is not None and r["letter_grade"] not in ("W", "I"):
                quality_points += r["grade_point"] * credits
                gpa_credits += credits

        cumulative_gpa = round(quality_points / gpa_credits, 2) if gpa_credits > 0 else 0.0

        return {
            "student": student,
            "courses": rows,
            "total_credits_attempted": total_credits_attempted,
            "total_credits_earned": total_credits_earned,
            "cumulative_gpa": cumulative_gpa,
        }
