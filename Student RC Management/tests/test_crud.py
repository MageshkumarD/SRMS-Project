"""
Integration & CRUD Operation Tests.
Tests full lifecycle of Students, Courses, Enrollments, and Academic GPAs.
"""

import os
import unittest
from pathlib import Path
from database.connection import DatabaseManager
from models.student import Student
from models.course import Course
from services.student_service import StudentService
from services.course_service import CourseService
from services.grade_service import GradeService


class TestCRUDOperations(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        test_db_path = str(Path(__file__).parent / "test_student_records.db")
        if os.path.exists(test_db_path):
            os.remove(test_db_path)

        cls.db = DatabaseManager(engine="sqlite")
        cls.db._sqlite_path = test_db_path
        cls.db.initialize_schema()

        cls.student_service = StudentService(cls.db)
        cls.course_service = CourseService(cls.db)
        cls.grade_service = GradeService(cls.db)

    @classmethod
    def tearDownClass(cls):
        test_db_path = Path(__file__).parent / "test_student_records.db"
        if test_db_path.exists():
            test_db_path.unlink()

    def test_01_student_lifecycle(self):
        # Create
        student = Student(
            student_code="TEST-001",
            first_name="Alice",
            last_name="Johnson",
            email="alice.j@university.edu",
            phone="+1-555-1234",
            date_of_birth="2002-06-15",
            enrollment_date="2021-09-01",
            status="Active",
        )
        s_id = self.student_service.create_student(student)
        self.assertGreater(s_id, 0)

        # Read
        fetched = self.student_service.get_by_id(s_id)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.student_code, "TEST-001")
        self.assertEqual(fetched.full_name, "Alice Johnson")

        # Update
        updated = self.student_service.update_student(s_id, {"first_name": "Alicia", "phone": "+1-555-9999"})
        self.assertTrue(updated)
        fetched_after = self.student_service.get_by_id(s_id)
        self.assertEqual(fetched_after.first_name, "Alicia")

        # Search
        results = self.student_service.search("Alicia")
        self.assertTrue(any(s.student_code == "TEST-001" for s in results))

    def test_02_course_lifecycle(self):
        # Create
        course = Course(
            course_code="CS501",
            course_name="Advanced Operating Systems",
            credits=4,
            description="Kernel development and concurrency",
            dept_code="CS",
            max_capacity=25,
        )
        c_id = self.course_service.create_course(course)
        self.assertGreater(c_id, 0)

        # Read
        fetched = self.course_service.get_by_code("CS501")
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.course_name, "Advanced Operating Systems")
        self.assertEqual(fetched.credits, 4)

        # Update
        self.course_service.update_course(c_id, {"max_capacity": 30})
        fetched_after = self.course_service.get_by_id(c_id)
        self.assertEqual(fetched_after.max_capacity, 30)

    def test_03_enrollment_and_gpa(self):
        # Create student and courses
        s = Student(
            student_code="TEST-002",
            first_name="Bob",
            last_name="Davis",
            email="bob.d@university.edu",
            date_of_birth="2003-03-20",
            enrollment_date="2022-09-01",
        )
        s_id = self.student_service.create_student(s)

        c1 = Course(course_code="MATH301", course_name="Complex Analysis", credits=3)
        c2 = Course(course_code="PHYS201", course_name="Thermodynamics", credits=4)
        c1_id = self.course_service.create_course(c1)
        c2_id = self.course_service.create_course(c2)

        # Enroll
        e1_id = self.grade_service.enroll_student(s_id, c1_id, "Fall 2026")
        e2_id = self.grade_service.enroll_student(s_id, c2_id, "Fall 2026")
        self.assertGreater(e1_id, 0)
        self.assertGreater(e2_id, 0)

        # Record Grades
        # MATH301: 95.0 -> 'A' (4.0 points, 3 credits = 12 quality points)
        self.grade_service.record_grade(e1_id, 95.0)
        # PHYS201: 85.0 -> 'B' (3.0 points, 4 credits = 12 quality points)
        self.grade_service.record_grade(e2_id, 85.0)

        # Expected GPA = (12 + 12) / (3 + 4) = 24 / 7 = 3.43
        transcript = self.student_service.get_transcript(s_id)
        self.assertEqual(transcript["total_credits_attempted"], 7)
        self.assertEqual(transcript["total_credits_earned"], 7)
        self.assertEqual(transcript["cumulative_gpa"], 3.43)

    def test_04_cascade_delete(self):
        # Create student, enroll in course
        s = Student(
            student_code="TEST-003",
            first_name="Charlie",
            last_name="Brown",
            email="charlie.b@university.edu",
            date_of_birth="2004-01-01",
            enrollment_date="2023-09-01",
        )
        s_id = self.student_service.create_student(s)
        c = self.course_service.get_by_code("CS501")
        e_id = self.grade_service.enroll_student(s_id, c.course_id, "Spring 2026")

        # Verify enrollment exists
        enr = self.grade_service.get_by_id(e_id)
        self.assertIsNotNone(enr)

        # Delete student -> should cascade delete enrollment
        self.student_service.delete_student(s_id)
        self.assertIsNone(self.student_service.get_by_id(s_id))
        self.assertIsNone(self.grade_service.get_by_id(e_id))


if __name__ == "__main__":
    unittest.main()
