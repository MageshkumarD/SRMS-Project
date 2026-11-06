"""
Reporting & Analytics Service.
Generates academic performance reports, honors rankings, and CSV/JSON data exports.
"""

import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from database.connection import db, DatabaseManager
import config


class ReportService:
    def __init__(self, db_manager: DatabaseManager = db):
        self.db = db_manager

    def get_honor_roll(self, min_gpa: float = 3.5, min_credits: int = 3, limit: int = 15) -> List[Dict[str, Any]]:
        """
        Retrieves top performing students meeting GPA and credit threshold.
        Computes weighted GPA via SQL aggregates with parameterization.
        """
        query = """
            SELECT
                s.student_id,
                s.student_code,
                s.first_name || ' ' || s.last_name AS student_name,
                s.email,
                s.status,
                SUM(c.credits) AS total_credits_attempted,
                SUM(CASE WHEN e.letter_grade NOT IN ('F', 'W', 'I') THEN c.credits ELSE 0 END) AS credits_earned,
                ROUND(SUM(e.grade_point * c.credits) / SUM(c.credits), 2) AS cumulative_gpa
            FROM students s
            JOIN enrollments e ON s.student_id = e.student_id
            JOIN courses c ON e.course_id = c.course_id
            WHERE e.grade_point IS NOT NULL
              AND e.status = 'Completed'
              AND s.status = 'Active'
            GROUP BY s.student_id, s.student_code, s.first_name, s.last_name, s.email, s.status
            HAVING cumulative_gpa >= ? AND total_credits_attempted >= ?
            ORDER BY cumulative_gpa DESC, credits_earned DESC
            LIMIT ?
        """
        return self.db.fetch_all(query, (min_gpa, min_credits, limit))

    def get_department_summary(self) -> List[Dict[str, Any]]:
        """Summarizes courses, active students, and enrollments grouped by department."""
        query = """
            SELECT
                COALESCE(d.dept_code, 'UNASSIGNED') AS dept_code,
                COALESCE(d.dept_name, 'General / Unassigned') AS dept_name,
                COUNT(DISTINCT c.course_id) AS total_courses,
                COUNT(e.enrollment_id) AS total_enrollments,
                COALESCE(ROUND(AVG(e.numeric_score), 2), 0.0) AS avg_score
            FROM departments d
            LEFT JOIN courses c ON d.dept_code = c.dept_code
            LEFT JOIN enrollments e ON c.course_id = e.course_id
            GROUP BY d.dept_code, d.dept_name
            ORDER BY total_enrollments DESC
        """
        return self.db.fetch_all(query)

    def get_overall_grade_distribution(self) -> List[Dict[str, Any]]:
        """Computes aggregate distribution of letter grades across all courses."""
        query = """
            SELECT
                letter_grade,
                COUNT(*) AS count,
                ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM enrollments WHERE letter_grade IS NOT NULL), 1) AS percentage
            FROM enrollments
            WHERE letter_grade IS NOT NULL
            GROUP BY letter_grade
            ORDER BY count DESC
        """
        return self.db.fetch_all(query)

    def export_students_csv(self, filename: Optional[str] = None) -> str:
        """Exports all student records to a CSV file."""
        target_path = Path(filename) if filename else config.EXPORTS_DIR / "students_export.csv"
        target_path.parent.mkdir(parents=True, exist_ok=True)

        rows = self.db.fetch_all("SELECT * FROM students ORDER BY student_id ASC")
        if not rows:
            headers = ["student_id", "student_code", "first_name", "last_name", "email", "phone", "date_of_birth", "enrollment_date", "status"]
        else:
            headers = list(rows[0].keys())

        with open(target_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(rows)

        return str(target_path)

    def export_grades_csv(self, filename: Optional[str] = None) -> str:
        """Exports all student grades and transcript records to a CSV file."""
        target_path = Path(filename) if filename else config.EXPORTS_DIR / "grades_export.csv"
        target_path.parent.mkdir(parents=True, exist_ok=True)

        query = """
            SELECT
                e.enrollment_id,
                s.student_code,
                s.first_name || ' ' || s.last_name AS student_name,
                s.email,
                c.course_code,
                c.course_name,
                c.credits,
                e.semester,
                e.numeric_score,
                e.letter_grade,
                e.grade_point,
                e.status,
                e.enrollment_date,
                e.grade_date
            FROM enrollments e
            JOIN students s ON e.student_id = s.student_id
            JOIN courses c ON e.course_id = c.course_id
            ORDER BY e.semester DESC, s.student_code ASC
        """
        rows = self.db.fetch_all(query)
        headers = [
            "enrollment_id", "student_code", "student_name", "email", "course_code",
            "course_name", "credits", "semester", "numeric_score", "letter_grade",
            "grade_point", "status", "enrollment_date", "grade_date"
        ]

        with open(target_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(rows)

        return str(target_path)

    def export_database_json(self, filename: Optional[str] = None) -> str:
        """Exports a full relational JSON backup of departments, students, courses, and enrollments."""
        target_path = Path(filename) if filename else config.EXPORTS_DIR / "database_backup.json"
        target_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "departments": self.db.fetch_all("SELECT * FROM departments"),
            "students": self.db.fetch_all("SELECT * FROM students"),
            "courses": self.db.fetch_all("SELECT * FROM courses"),
            "enrollments": self.db.fetch_all("SELECT * FROM enrollments"),
        }

        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)

        return str(target_path)
