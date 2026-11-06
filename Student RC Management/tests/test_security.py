"""
Security & SQL Injection Vulnerability Test Suite.
Verifies that database access is strictly secured via parameterized queries.
"""

import os
import unittest
from pathlib import Path
from database.connection import DatabaseManager
from models.student import Student
from services.student_service import StudentService
from services.course_service import CourseService
from utils.validators import ValidationError


class TestSQLInjectionSecurity(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        test_db_path = str(Path(__file__).parent / "test_security.db")
        if os.path.exists(test_db_path):
            os.remove(test_db_path)

        cls.db = DatabaseManager(engine="sqlite")
        cls.db._sqlite_path = test_db_path
        cls.db.initialize_schema()

        cls.student_service = StudentService(cls.db)
        cls.course_service = CourseService(cls.db)

        # Seed two control students
        cls.student_service.create_student(
            Student(
                student_code="SEC-001",
                first_name="Secure",
                last_name="UserOne",
                email="secure1@example.com",
                date_of_birth="2000-01-01",
                enrollment_date="2020-09-01",
            )
        )
        cls.student_service.create_student(
            Student(
                student_code="SEC-002",
                first_name="Secure",
                last_name="UserTwo",
                email="secure2@example.com",
                date_of_birth="2001-02-02",
                enrollment_date="2021-09-01",
            )
        )

    @classmethod
    def tearDownClass(cls):
        test_db_path = Path(__file__).parent / "test_security.db"
        if test_db_path.exists():
            test_db_path.unlink()

    def test_search_tautology_attack(self):
        """Testing classical ' OR '1'='1 bypass attack in search parameter."""
        attack_payload = "' OR '1'='1"
        results = self.student_service.search(attack_payload)
        # In a vulnerable app, this returns all records in the table.
        # With parameterized queries, it only matches a student literally named or coded with that string.
        self.assertEqual(len(results), 0)

    def test_search_union_attack(self):
        """Testing UNION SELECT attack to extract sqlite_master / schemas."""
        attack_payload = "' UNION SELECT 1, 'HACK', 'HACK', 'hacked@hack.com', '', '2000-01-01', '2020-01-01', 'Active', '', '' --"
        results = self.student_service.search(attack_payload)
        self.assertEqual(len(results), 0)

    def test_search_drop_table_injection(self):
        """Testing stacked query injection attempting to drop students table."""
        attack_payload = "test'; DROP TABLE students; --"
        # Should execute safely without executing DROP TABLE
        results = self.student_service.search(attack_payload)
        self.assertEqual(len(results), 0)

        # Confirm students table is completely intact
        count = self.db.fetch_one("SELECT COUNT(*) AS c FROM students")["c"]
        self.assertEqual(count, 2)

    def test_student_code_injection_in_lookup(self):
        """Testing injection through student code query."""
        payload = "SEC-001' OR 1=1 --"
        student = self.student_service.get_by_code(payload)
        self.assertIsNone(student)

    def test_input_validation_neutralizes_malicious_names(self):
        """Testing that input validation layer rejects malicious names before database query."""
        with self.assertRaises(ValidationError):
            Student(
                student_code="HACK-01",
                first_name="<script>alert(1)</script>",
                last_name="Smith",
                email="smith@example.com",
                date_of_birth="2000-01-01",
                enrollment_date="2020-09-01",
            )


if __name__ == "__main__":
    unittest.main()
