"""
Course Service Layer.
Encapsulates all Course business logic, capacity management, and roster retrieval.
"""

from typing import Any, Dict, List, Optional
from database.connection import db, DatabaseManager
from models.course import Course
from utils.validators import (
    ValidationError,
    validate_course_code,
    validate_course_name,
    validate_credits,
    validate_capacity,
)


class CourseService:
    def __init__(self, db_manager: DatabaseManager = db):
        self.db = db_manager

    def create_course(self, course: Course) -> int:
        """Creates a new course record."""
        existing = self.get_by_code(course.course_code)
        if existing:
            raise ValidationError(f"Course code '{course.course_code}' is already registered.")

        # Ensure department exists if specified
        if course.dept_code:
            dept = self.db.fetch_one("SELECT * FROM departments WHERE dept_code = ?", (course.dept_code,))
            if not dept:
                # Auto-register department
                self.db.execute(
                    "INSERT OR IGNORE INTO departments (dept_code, dept_name) VALUES (?, ?)",
                    (course.dept_code, f"{course.dept_code} Department"),
                )

        query = """
            INSERT INTO courses (
                course_code, course_name, description, credits, dept_code, max_capacity
            ) VALUES (?, ?, ?, ?, ?, ?)
        """
        params = (
            course.course_code,
            course.course_name,
            course.description,
            course.credits,
            course.dept_code,
            course.max_capacity,
        )
        return self.db.execute(query, params)

    def get_by_id(self, course_id: int) -> Optional[Course]:
        """Fetches a course by its primary key."""
        query = "SELECT * FROM courses WHERE course_id = ?"
        row = self.db.fetch_one(query, (course_id,))
        return Course.from_row(row) if row else None

    def get_by_code(self, course_code: str) -> Optional[Course]:
        """Fetches a course by its unique course code."""
        query = "SELECT * FROM courses WHERE course_code = ?"
        row = self.db.fetch_one(query, (course_code.strip().upper(),))
        return Course.from_row(row) if row else None

    def list_all(self, dept_code: Optional[str] = None, limit: int = 100, offset: int = 0) -> List[Course]:
        """Lists courses with optional department filter and pagination."""
        if dept_code:
            query = "SELECT * FROM courses WHERE dept_code = ? ORDER BY course_code ASC LIMIT ? OFFSET ?"
            rows = self.db.fetch_all(query, (dept_code.strip().upper(), limit, offset))
        else:
            query = "SELECT * FROM courses ORDER BY course_code ASC LIMIT ? OFFSET ?"
            rows = self.db.fetch_all(query, (limit, offset))
        return [Course.from_row(r) for r in rows]

    def search(self, search_term: str) -> List[Course]:
        """Searches courses matching query against code, name, or description."""
        cleaned = search_term.strip()
        pattern = f"%{cleaned}%"
        query = """
            SELECT * FROM courses
            WHERE course_code LIKE ?
               OR course_name LIKE ?
               OR dept_code LIKE ?
            ORDER BY course_code
        """
        rows = self.db.fetch_all(query, (pattern, pattern, pattern))
        return [Course.from_row(r) for r in rows]

    def update_course(self, course_id: int, updates: Dict[str, Any]) -> bool:
        """Updates designated fields of an existing course."""
        course = self.get_by_id(course_id)
        if not course:
            raise ValidationError(f"Course with ID {course_id} not found.")

        clauses = []
        params = []

        if "course_name" in updates and updates["course_name"]:
            name = validate_course_name(updates["course_name"])
            clauses.append("course_name = ?")
            params.append(name)

        if "credits" in updates and updates["credits"] is not None:
            credits_val = validate_credits(updates["credits"])
            clauses.append("credits = ?")
            params.append(credits_val)

        if "description" in updates:
            clauses.append("description = ?")
            params.append(updates["description"])

        if "dept_code" in updates:
            dept = updates["dept_code"].strip().upper() if updates["dept_code"] else None
            clauses.append("dept_code = ?")
            params.append(dept)

        if "max_capacity" in updates and updates["max_capacity"] is not None:
            cap = validate_capacity(updates["max_capacity"])
            clauses.append("max_capacity = ?")
            params.append(cap)

        if not clauses:
            return False

        params.append(course_id)
        query = f"UPDATE courses SET {', '.join(clauses)} WHERE course_id = ?"
        self.db.execute(query, tuple(params))
        return True

    def delete_course(self, course_id: int) -> bool:
        """Deletes a course by ID. Enrollments will be removed via cascade."""
        course = self.get_by_id(course_id)
        if not course:
            raise ValidationError(f"Course with ID {course_id} does not exist.")
        query = "DELETE FROM courses WHERE course_id = ?"
        self.db.execute(query, (course_id,))
        return True

    def get_roster(self, course_id: int, semester: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieves list of students enrolled in the course with current status and grade."""
        course = self.get_by_id(course_id)
        if not course:
            raise ValidationError(f"Course with ID {course_id} does not exist.")

        if semester:
            query = """
                SELECT
                    e.enrollment_id,
                    s.student_id,
                    s.student_code,
                    s.first_name,
                    s.last_name,
                    s.email,
                    e.semester,
                    e.numeric_score,
                    e.letter_grade,
                    e.status,
                    e.enrollment_date
                FROM enrollments e
                JOIN students s ON e.student_id = s.student_id
                WHERE e.course_id = ? AND e.semester = ?
                ORDER BY s.last_name, s.first_name
            """
            return self.db.fetch_all(query, (course_id, semester))
        else:
            query = """
                SELECT
                    e.enrollment_id,
                    s.student_id,
                    s.student_code,
                    s.first_name,
                    s.last_name,
                    s.email,
                    e.semester,
                    e.numeric_score,
                    e.letter_grade,
                    e.status,
                    e.enrollment_date
                FROM enrollments e
                JOIN students s ON e.student_id = s.student_id
                WHERE e.course_id = ?
                ORDER BY e.semester DESC, s.last_name, s.first_name
            """
            return self.db.fetch_all(query, (course_id,))
