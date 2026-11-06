"""
Unit Tests for Data Validators and Business Logic.
"""

import unittest
from datetime import date
from utils.validators import (
    ValidationError,
    validate_name,
    validate_student_code,
    validate_email,
    validate_phone,
    validate_date,
    validate_dob,
    validate_enrollment_date,
    validate_course_code,
    validate_credits,
    validate_capacity,
    score_to_letter_grade,
    letter_grade_to_points,
)


class TestValidators(unittest.TestCase):

    def test_valid_names(self):
        self.assertEqual(validate_name("John"), "John")
        self.assertEqual(validate_name("Mary-Jane"), "Mary-Jane")
        self.assertEqual(validate_name("O'Connor"), "O'Connor")
        self.assertEqual(validate_name("Renée"), "Renée")

    def test_invalid_names(self):
        with self.assertRaises(ValidationError):
            validate_name("")
        with self.assertRaises(ValidationError):
            validate_name("A")
        with self.assertRaises(ValidationError):
            validate_name("User123")
        with self.assertRaises(ValidationError):
            validate_name("Drop table;")

    def test_student_code(self):
        self.assertEqual(validate_student_code("stu-1001"), "STU-1001")
        self.assertEqual(validate_student_code("S12345"), "S12345")
        with self.assertRaises(ValidationError):
            validate_student_code("")
        with self.assertRaises(ValidationError):
            validate_student_code("AB")  # Too short

    def test_email(self):
        self.assertEqual(validate_email("TEST@Domain.COM"), "test@domain.com")
        self.assertEqual(validate_email("user.name+tag@sub.example.org"), "user.name+tag@sub.example.org")
        with self.assertRaises(ValidationError):
            validate_email("notanemail")
        with self.assertRaises(ValidationError):
            validate_email("test@")
        with self.assertRaises(ValidationError):
            validate_email("@domain.com")

    def test_date_and_dob(self):
        self.assertEqual(validate_date("2024-05-15"), "2024-05-15")
        with self.assertRaises(ValidationError):
            validate_date("15/05/2024")
        with self.assertRaises(ValidationError):
            validate_date("invalid-date")

        # DOB age limits
        self.assertEqual(validate_dob("2000-01-01"), "2000-01-01")
        # In the future
        future_year = date.today().year + 1
        with self.assertRaises(ValidationError):
            validate_dob(f"{future_year}-01-01")

    def test_course_code_and_credits(self):
        self.assertEqual(validate_course_code("cs101"), "CS101")
        self.assertEqual(validate_course_code("MATH-201"), "MATH-201")
        self.assertEqual(validate_credits(3), 3)
        self.assertEqual(validate_credits("4"), 4)
        with self.assertRaises(ValidationError):
            validate_credits(0)
        with self.assertRaises(ValidationError):
            validate_credits(7)

    def test_score_mapping(self):
        grade, pts = score_to_letter_grade(98.5)
        self.assertEqual(grade, "A+")
        self.assertEqual(pts, 4.0)

        grade, pts = score_to_letter_grade(85.0)
        self.assertEqual(grade, "B")
        self.assertEqual(pts, 3.0)

        grade, pts = score_to_letter_grade(55.0)
        self.assertEqual(grade, "F")
        self.assertEqual(pts, 0.0)

        self.assertEqual(letter_grade_to_points("A"), 4.0)
        self.assertEqual(letter_grade_to_points("B+"), 3.3)


if __name__ == "__main__":
    unittest.main()
