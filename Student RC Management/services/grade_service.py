"""
Grade and Enrollment Service Layer.
Manages student enrollment, course capacity enforcement, grade calculations,
and statistical evaluations with strict transaction safety.
"""

from datetime import date
from typing import Any, Dict, List, Optional
from database.connection import db, DatabaseManager
from models.enrollment import Enrollment
from utils.validators import (
    ValidationError,
    validate_score,
    validate_letter_grade,
    score_to_letter_grade,
    letter_grade_to_points,
    validate_semester,
)


class GradeService:
    def __init__(self, db_manager: DatabaseManager = db):
        self.db = db_manager

    def enroll_student(self, student_id: int, course_id: int, semester: str) -> int:
        """
        Enrolls a student in a course for a given semester.
        Enforces:
        - Student existence and Active status.
        - Course existence.
        - Course maximum capacity limits.
        - Prevent duplicate enrollment in the same semester.
        """
        semester = validate_semester(semester)

        # 1. Verify student exists and is active
        student = self.db.fetch_one("SELECT * FROM students WHERE student_id = ?", (student_id,))
        if not student:
            raise ValidationError(f"Student with ID {student_id} not found.")
        if student["status"] != "Active":
            raise ValidationError(
                f"Cannot enroll student '{student['first_name']} {student['last_name']}': Status is '{student['status']}'."
            )

        # 2. Verify course exists
        course = self.db.fetch_one("SELECT * FROM courses WHERE course_id = ?", (course_id,))
        if not course:
            raise ValidationError(f"Course with ID {course_id} not found.")

        # 3. Check duplicate enrollment
        duplicate = self.db.fetch_one(
            "SELECT * FROM enrollments WHERE student_id = ? AND course_id = ? AND semester = ?",
            (student_id, course_id, semester),
        )
        if duplicate:
            raise ValidationError(
                f"Student is already enrolled in {course['course_code']} for {semester} (Status: {duplicate['status']})."
            )

        # 4. Check capacity constraint
        active_count_row = self.db.fetch_one(
            """
            SELECT COUNT(*) AS active_count
            FROM enrollments
            WHERE course_id = ? AND semester = ? AND status != 'Dropped'
            """,
            (course_id, semester),
        )
        current_enrolled = active_count_row["active_count"] if active_count_row else 0
        if current_enrolled >= course["max_capacity"]:
            raise ValidationError(
                f"Course {course['course_code']} has reached maximum capacity ({current_enrolled}/{course['max_capacity']})."
            )

        # 5. Insert enrollment
        today_str = date.today().strftime("%Y-%m-%d")
        query = """
            INSERT INTO enrollments (
                student_id, course_id, semester, status, enrollment_date
            ) VALUES (?, ?, ?, 'Enrolled', ?)
        """
        return self.db.execute(query, (student_id, course_id, semester, today_str))

    def record_grade(self, enrollment_id: int, numeric_score: float) -> bool:
        """
        Records or updates a grade based on numeric score (0-100).
        Automatically computes letter grade, GPA points, sets status to 'Completed',
        and stamps grading date.
        """
        enrollment = self.get_by_id(enrollment_id)
        if not enrollment:
            raise ValidationError(f"Enrollment record with ID {enrollment_id} does not exist.")

        if enrollment["status"] == "Dropped":
            raise ValidationError("Cannot assign grade to a dropped course.")

        score = validate_score(numeric_score)
        letter_grade, points = score_to_letter_grade(score)
        today_str = date.today().strftime("%Y-%m-%d")

        query = """
            UPDATE enrollments
            SET numeric_score = ?,
                letter_grade = ?,
                grade_point = ?,
                status = 'Completed',
                grade_date = ?
            WHERE enrollment_id = ?
        """
        self.db.execute(query, (score, letter_grade, points, today_str, enrollment_id))
        return True

    def assign_letter_grade(self, enrollment_id: int, letter_grade: str) -> bool:
        """Assigns letter grade directly (e.g. for transferred or pass/fail credits)."""
        enrollment = self.get_by_id(enrollment_id)
        if not enrollment:
            raise ValidationError(f"Enrollment with ID {enrollment_id} not found.")

        grade = validate_letter_grade(letter_grade)
        points = letter_grade_to_points(grade)
        today_str = date.today().strftime("%Y-%m-%d")

        query = """
            UPDATE enrollments
            SET letter_grade = ?,
                grade_point = ?,
                status = 'Completed',
                grade_date = ?
            WHERE enrollment_id = ?
        """
        self.db.execute(query, (grade, points, today_str, enrollment_id))
        return True

    def drop_course(self, enrollment_id: int) -> bool:
        """Marks enrollment as 'Dropped' with withdrawal status."""
        enrollment = self.get_by_id(enrollment_id)
        if not enrollment:
            raise ValidationError(f"Enrollment with ID {enrollment_id} does not exist.")

        query = """
            UPDATE enrollments
            SET status = 'Dropped',
                letter_grade = 'W',
                numeric_score = NULL,
                grade_point = NULL,
                grade_date = ?
            WHERE enrollment_id = ?
        """
        today_str = date.today().strftime("%Y-%m-%d")
        self.db.execute(query, (today_str, enrollment_id))
        return True

    def delete_enrollment(self, enrollment_id: int) -> bool:
        """Deletes an enrollment record entirely."""
        enrollment = self.get_by_id(enrollment_id)
        if not enrollment:
            raise ValidationError(f"Enrollment with ID {enrollment_id} does not exist.")
        self.db.execute("DELETE FROM enrollments WHERE enrollment_id = ?", (enrollment_id,))
        return True

    def get_by_id(self, enrollment_id: int) -> Optional[Dict[str, Any]]:
        """Retrieves full enrollment information including student and course names."""
        query = """
            SELECT
                e.*,
                s.student_code,
                s.first_name,
                s.last_name,
                s.email,
                c.course_code,
                c.course_name,
                c.credits
            FROM enrollments e
            JOIN students s ON e.student_id = s.student_id
            JOIN courses c ON e.course_id = c.course_id
            WHERE e.enrollment_id = ?
        """
        return self.db.fetch_one(query, (enrollment_id,))

    def list_enrollments(
        self,
        student_id: Optional[int] = None,
        course_id: Optional[int] = None,
        semester: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Queries enrollment records with dynamic parameterized filtering."""
        clauses = []
        params = []

        if student_id:
            clauses.append("e.student_id = ?")
            params.append(student_id)
        if course_id:
            clauses.append("e.course_id = ?")
            params.append(course_id)
        if semester:
            clauses.append("e.semester = ?")
            params.append(semester)
        if status:
            clauses.append("e.status = ?")
            params.append(status)

        where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""

        query = f"""
            SELECT
                e.enrollment_id,
                s.student_code,
                s.first_name || ' ' || s.last_name AS student_name,
                c.course_code,
                c.course_name,
                c.credits,
                e.semester,
                e.numeric_score,
                e.letter_grade,
                e.grade_point,
                e.status,
                e.enrollment_date
            FROM enrollments e
            JOIN students s ON e.student_id = s.student_id
            JOIN courses c ON e.course_id = c.course_id
            {where_sql}
            ORDER BY e.semester DESC, c.course_code ASC
        """
        return self.db.fetch_all(query, tuple(params))

    def get_course_stats(self, course_id: int, semester: Optional[str] = None) -> Dict[str, Any]:
        """Calculates statistical performance metrics for a course."""
        course = self.db.fetch_one("SELECT * FROM courses WHERE course_id = ?", (course_id,))
        if not course:
            raise ValidationError(f"Course with ID {course_id} does not exist.")

        params = [course_id]
        sem_clause = ""
        if semester:
            sem_clause = "AND semester = ?"
            params.append(semester)

        query = f"""
            SELECT
                numeric_score,
                letter_grade,
                grade_point
            FROM enrollments
            WHERE course_id = ? AND status = 'Completed' AND numeric_score IS NOT NULL
            {sem_clause}
        """
        rows = self.db.fetch_all(query, tuple(params))

        if not rows:
            return {
                "course": course,
                "semester": semester or "All Semesters",
                "count": 0,
                "average_score": None,
                "highest_score": None,
                "lowest_score": None,
                "pass_rate": None,
                "grade_distribution": {},
            }

        scores = [r["numeric_score"] for r in rows]
        grades = [r["letter_grade"] for r in rows]

        avg_score = round(sum(scores) / len(scores), 2)
        high_score = round(max(scores), 2)
        low_score = round(min(scores), 2)

        passing_count = sum(1 for g in grades if g not in ("F", "W", "I"))
        pass_rate = round((passing_count / len(grades)) * 100, 1)

        distribution = {}
        for g in grades:
            distribution[g] = distribution.get(g, 0) + 1

        return {
            "course": course,
            "semester": semester or "All Semesters",
            "count": len(rows),
            "average_score": avg_score,
            "highest_score": high_score,
            "lowest_score": low_score,
            "pass_rate": pass_rate,
            "grade_distribution": distribution,
        }
