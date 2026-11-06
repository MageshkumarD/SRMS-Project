"""
Unit Tests for Interactive Web Application Routes and API Endpoints.
"""

import unittest
from app import app


class TestWebApp(unittest.TestCase):

    def setUp(self):
        self.client = app.test_client()
        self.client.testing = True

    def test_pages_render(self):
        routes = ["/", "/students", "/courses", "/grades", "/reports"]
        for route in routes:
            response = self.client.get(route)
            self.assertEqual(response.status_code, 200, f"Route {route} failed")

    def test_api_students(self):
        response = self.client.get("/api/students")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data.get("success"))
        self.assertIsInstance(data.get("students"), list)

    def test_api_transcripts(self):
        response = self.client.get("/api/students/1/transcript")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data.get("success"))
        self.assertIn("cumulative_gpa", data)

    def test_csv_exports(self):
        r1 = self.client.get("/export/students.csv")
        self.assertEqual(r1.status_code, 200)
        self.assertIn("text/csv", r1.content_type)

        r2 = self.client.get("/export/grades.csv")
        self.assertEqual(r2.status_code, 200)
        self.assertIn("text/csv", r2.content_type)


if __name__ == "__main__":
    unittest.main()
