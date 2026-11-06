"""
Database Seeding Module.
Populates realistic departments, students, courses, and graded enrollments for demonstration.
"""

from database.connection import db, DatabaseManager


def seed_database(db_manager: DatabaseManager = db, reset: bool = False) -> None:
    """Populates realistic academic records into the database."""
    db_manager.initialize_schema()

    if reset:
        with db_manager.transaction() as conn:
            conn.execute("DELETE FROM enrollments")
            conn.execute("DELETE FROM courses")
            conn.execute("DELETE FROM students")
            conn.execute("DELETE FROM departments")

    # Check if data already exists
    existing = db_manager.fetch_one("SELECT COUNT(*) AS c FROM students")
    if existing and existing["c"] > 0 and not reset:
        return

    # 1. Departments
    departments = [
        ("CS", "Computer Science & Engineering"),
        ("MATH", "Department of Mathematics"),
        ("PHYS", "Department of Physics"),
        ("EE", "Electrical Engineering"),
        ("BIO", "Biological Sciences"),
    ]
    for code, name in departments:
        db_manager.execute(
            "INSERT OR IGNORE INTO departments (dept_code, dept_name) VALUES (?, ?)",
            (code, name),
        )

    # 2. Students
    students = [
        ("STU-1001", "Emma", "Watson", "emma.watson@university.edu", "+1-555-0101", "2004-04-15", "2023-09-01", "Active"),
        ("STU-1002", "Liam", "Chen", "liam.chen@university.edu", "+1-555-0102", "2003-11-20", "2022-09-01", "Active"),
        ("STU-1003", "Sophia", "Rodriguez", "sophia.r@university.edu", "+1-555-0103", "2004-02-10", "2023-09-01", "Active"),
        ("STU-1004", "Noah", "Patel", "noah.patel@university.edu", "+1-555-0104", "2002-08-30", "2021-09-01", "Active"),
        ("STU-1005", "Ava", "Kowalski", "ava.k@university.edu", "+1-555-0105", "2003-05-18", "2022-09-01", "Active"),
        ("STU-1006", "Lucas", "Dubois", "lucas.d@university.edu", "+1-555-0106", "2004-09-12", "2023-09-01", "Active"),
        ("STU-1007", "Mia", "Tanaka", "mia.tanaka@university.edu", "+1-555-0107", "2003-12-05", "2022-09-01", "Active"),
        ("STU-1008", "Ethan", "Miller", "ethan.m@university.edu", "+1-555-0108", "2001-07-22", "2020-09-01", "Graduated"),
        ("STU-1009", "Isabella", "Silva", "isabella.s@university.edu", "+1-555-0109", "2004-03-14", "2023-09-01", "Active"),
        ("STU-1010", "Alexander", "Wright", "alex.w@university.edu", "+1-555-0110", "2003-10-09", "2022-09-01", "Suspended"),
    ]
    for s in students:
        db_manager.execute(
            """
            INSERT OR IGNORE INTO students (
                student_code, first_name, last_name, email,
                phone, date_of_birth, enrollment_date, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            s,
        )

    # 3. Courses
    courses = [
        ("CS101", "Introduction to Computer Science", "Foundations of algorithms and Python programming", 4, "CS", 35),
        ("CS201", "Data Structures & Algorithms", "Linear and non-linear data structures, trees, graphs", 4, "CS", 30),
        ("CS301", "Database Systems & Design", "Relational database modeling, SQL, normalization, and ACID", 3, "CS", 30),
        ("MATH101", "Calculus I", "Differential and integral calculus of single variables", 4, "MATH", 40),
        ("MATH201", "Linear Algebra", "Vector spaces, linear transformations, matrices, eigenvalues", 3, "MATH", 35),
        ("PHYS101", "Classical Mechanics", "Newtonian mechanics, energy conservation, oscillations", 4, "PHYS", 30),
        ("EE101", "Circuits and Electronics", "Circuit analysis, Ohm's and Kirchhoff's laws, AC circuits", 3, "EE", 25),
        ("BIO101", "General Biology", "Cell biology, genetics, evolution and cellular ecology", 3, "BIO", 40),
    ]
    for c in courses:
        db_manager.execute(
            """
            INSERT OR IGNORE INTO courses (
                course_code, course_name, description, credits, dept_code, max_capacity
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            c,
        )

    # Map student_code to id and course_code to id
    stu_map = {row["student_code"]: row["student_id"] for row in db_manager.fetch_all("SELECT student_code, student_id FROM students")}
    crs_map = {row["course_code"]: row["course_id"] for row in db_manager.fetch_all("SELECT course_code, course_id FROM courses")}

    # 4. Enrollments & Graded Records
    # (student_code, course_code, semester, score, letter, points, status, enroll_date, grade_date)
    enrollment_data = [
        ("STU-1001", "CS101", "Fall 2025", 95.5, "A", 4.0, "Completed", "2025-09-05", "2025-12-20"),
        ("STU-1001", "MATH101", "Fall 2025", 92.0, "A-", 3.7, "Completed", "2025-09-05", "2025-12-20"),
        ("STU-1001", "CS201", "Spring 2026", 98.0, "A+", 4.0, "Completed", "2026-01-10", "2026-05-15"),
        ("STU-1001", "CS301", "Fall 2026", None, None, None, "Enrolled", "2026-09-01", None),

        ("STU-1002", "CS101", "Fall 2024", 88.5, "B+", 3.3, "Completed", "2024-09-05", "2024-12-20"),
        ("STU-1002", "CS201", "Spring 2025", 91.0, "A-", 3.7, "Completed", "2025-01-10", "2025-05-15"),
        ("STU-1002", "CS301", "Fall 2025", 86.0, "B", 3.0, "Completed", "2025-09-05", "2025-12-20"),
        ("STU-1002", "MATH201", "Spring 2026", 84.5, "B", 3.0, "Completed", "2026-01-10", "2026-05-15"),

        ("STU-1003", "CS101", "Fall 2025", 94.0, "A", 4.0, "Completed", "2025-09-05", "2025-12-20"),
        ("STU-1003", "MATH101", "Fall 2025", 96.0, "A", 4.0, "Completed", "2025-09-05", "2025-12-20"),
        ("STU-1003", "PHYS101", "Spring 2026", 89.0, "B+", 3.3, "Completed", "2026-01-10", "2026-05-15"),

        ("STU-1004", "MATH101", "Fall 2023", 78.0, "C+", 2.3, "Completed", "2023-09-05", "2023-12-20"),
        ("STU-1004", "MATH201", "Spring 2024", 82.0, "B-", 2.7, "Completed", "2024-01-10", "2024-05-15"),
        ("STU-1004", "CS101", "Fall 2024", 75.0, "C", 2.0, "Completed", "2024-09-05", "2024-12-20"),

        ("STU-1005", "BIO101", "Fall 2024", 91.5, "A-", 3.7, "Completed", "2024-09-05", "2024-12-20"),
        ("STU-1005", "PHYS101", "Spring 2025", 87.0, "B+", 3.3, "Completed", "2025-01-10", "2025-05-15"),

        ("STU-1006", "EE101", "Fall 2025", 83.0, "B", 3.0, "Completed", "2025-09-05", "2025-12-20"),
        ("STU-1006", "MATH101", "Spring 2026", 81.0, "B-", 2.7, "Completed", "2026-01-10", "2026-05-15"),

        ("STU-1007", "CS101", "Fall 2024", 97.0, "A+", 4.0, "Completed", "2024-09-05", "2024-12-20"),
        ("STU-1007", "CS201", "Spring 2025", 96.5, "A", 4.0, "Completed", "2025-01-10", "2025-05-15"),
        ("STU-1007", "CS301", "Fall 2025", 99.0, "A+", 4.0, "Completed", "2025-09-05", "2025-12-20"),

        ("STU-1009", "CS101", "Fall 2025", 90.0, "A-", 3.7, "Completed", "2025-09-05", "2025-12-20"),
        ("STU-1009", "MATH101", "Spring 2026", 88.0, "B+", 3.3, "Completed", "2026-01-10", "2026-05-15"),
    ]

    for s_code, c_code, sem, score, l_grade, gp, status, e_date, g_date in enrollment_data:
        if s_code in stu_map and c_code in crs_map:
            db_manager.execute(
                """
                INSERT OR IGNORE INTO enrollments (
                    student_id, course_id, semester, numeric_score,
                    letter_grade, grade_point, status, enrollment_date, grade_date
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (stu_map[s_code], crs_map[c_code], sem, score, l_grade, gp, status, e_date, g_date),
            )


if __name__ == "__main__":
    print("Seeding database with sample records...")
    seed_database(reset=True)
    print("Seeding successfully completed.")
