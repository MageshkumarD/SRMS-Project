"""
Menu Handler & User Workflow Controller.
Orchestrates CLI navigation, input processing, and service invocations
with comprehensive error handling and tabular reporting.
"""

import sys
from datetime import date
from typing import Optional

import config
from database.connection import db, DatabaseManager
from database.seed_data import seed_database
from models.student import Student
from models.course import Course
from services.student_service import StudentService
from services.course_service import CourseService
from services.grade_service import GradeService
from services.report_service import ReportService
from utils.validators import ValidationError, validate_date
from utils.table_formatter import format_table, format_card
from cli.ui import (
    clear_screen,
    print_banner,
    print_header,
    print_success,
    print_error,
    print_warning,
    print_info,
    prompt_string,
    prompt_int,
    prompt_float,
    prompt_choice,
    pause,
    BOLD,
    CYAN,
    YELLOW,
    RESET,
)


class MenuHandler:
    def __init__(self, db_manager: DatabaseManager = db):
        self.db = db_manager
        self.student_service = StudentService(self.db)
        self.course_service = CourseService(self.db)
        self.grade_service = GradeService(self.db)
        self.report_service = ReportService(self.db)

    def start(self) -> None:
        """Main application lifecycle loop."""
        try:
            self.db.initialize_schema()
        except Exception as e:
            print_error(f"Failed to initialize database: {e}")
            pause()
            return

        while True:
            clear_screen()
            print_banner()
            print(f"  Active Engine: {CYAN}{config.DB_ENGINE.upper()}{RESET} | Status: {config.SQLITE_DB_PATH if config.DB_ENGINE == 'sqlite' else config.MYSQL_CONFIG['host']}")
            print("-" * 75)
            print(f"  {BOLD}[1]{RESET} 🎓  Student Management")
            print(f"  {BOLD}[2]{RESET} 📚  Course Management")
            print(f"  {BOLD}[3]{RESET} 📝  Grades & Enrollments")
            print(f"  {BOLD}[4]{RESET} 📊  Reports & Analytics")
            print(f"  {BOLD}[5]{RESET} ⚙️  Database & System Utilities")
            print(f"  {BOLD}[0]{RESET} 🚪  Exit Application")
            print("-" * 75)

            choice = prompt_string("Enter your choice [0-5]", required=True)

            if choice == "1":
                self.student_menu()
            elif choice == "2":
                self.course_menu()
            elif choice == "3":
                self.grade_menu()
            elif choice == "4":
                self.reports_menu()
            elif choice == "5":
                self.system_menu()
            elif choice == "0":
                print_info("Thank you for using Student Records Management System. Goodbye!")
                sys.exit(0)
            else:
                print_error("Invalid selection. Please choose an option from the menu.")
                pause()

    # =========================================================================
    # 1. STUDENT MANAGEMENT SUBMENU
    # =========================================================================
    def student_menu(self) -> None:
        while True:
            clear_screen()
            print_header("Student Management")
            print(f"  {BOLD}[1]{RESET} Add New Student")
            print(f"  {BOLD}[2]{RESET} View All Students")
            print(f"  {BOLD}[3]{RESET} Search Student (by ID, Code, Name, Email)")
            print(f"  {BOLD}[4]{RESET} Update Student Information")
            print(f"  {BOLD}[5]{RESET} Delete Student Record")
            print(f"  {BOLD}[6]{RESET} View Student Transcript & Academic Report")
            print(f"  {BOLD}[0]{RESET} Back to Main Menu")

            choice = prompt_string("Select option [0-6]")
            if choice == "1":
                self._action_add_student()
            elif choice == "2":
                self._action_view_all_students()
            elif choice == "3":
                self._action_search_students()
            elif choice == "4":
                self._action_update_student()
            elif choice == "5":
                self._action_delete_student()
            elif choice == "6":
                self._action_view_transcript()
            elif choice == "0":
                break
            else:
                print_error("Invalid selection.")
                pause()

    def _action_add_student(self) -> None:
        print_header("Add New Student")
        try:
            student_code = prompt_string("Student ID Code (e.g. STU-1011)")
            first_name = prompt_string("First Name")
            last_name = prompt_string("Last Name")
            email = prompt_string("Email Address")
            phone = prompt_string("Phone Number (optional)", default="")
            dob = prompt_string("Date of Birth (YYYY-MM-DD)")
            today_str = date.today().strftime("%Y-%m-%d")
            enroll_date = prompt_string("Enrollment Date (YYYY-MM-DD)", default=today_str)
            status = prompt_choice("Select Status:", ["Active", "Suspended", "Graduated", "Withdrawn"], default="Active")

            new_student = Student(
                student_code=student_code,
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone=phone or None,
                date_of_birth=dob,
                enrollment_date=enroll_date,
                status=status,
            )

            student_id = self.student_service.create_student(new_student)
            print_success(f"Student '{new_student.full_name}' added successfully (Assigned Database ID: {student_id}).")
        except ValidationError as ve:
            print_error(f"Validation failed: {ve}")
        except Exception as ex:
            print_error(f"Failed to create student: {ex}")
        pause()

    def _action_view_all_students(self) -> None:
        print_header("All Registered Students")
        students = self.student_service.list_all()
        if not students:
            print_warning("No student records found in the database.")
        else:
            headers = ["ID", "Code", "Name", "Email", "Phone", "Status", "Enrolled Date"]
            rows = [
                [
                    s.student_id,
                    s.student_code,
                    s.full_name,
                    s.email,
                    s.phone or "-",
                    s.status,
                    s.enrollment_date,
                ]
                for s in students
            ]
            print(format_table(headers, rows, title=f"Student Registry (Total: {len(students)})"))
        pause()

    def _action_search_students(self) -> None:
        print_header("Search Students")
        term = prompt_string("Enter search keyword (Code, Name, or Email)")
        results = self.student_service.search(term)
        if not results:
            print_warning(f"No students matching '{term}' found.")
        else:
            headers = ["ID", "Code", "Name", "Email", "Status", "DOB"]
            rows = [
                [s.student_id, s.student_code, s.full_name, s.email, s.status, s.date_of_birth]
                for s in results
            ]
            print(format_table(headers, rows, title=f"Matching Students ({len(results)} found)"))
        pause()

    def _action_update_student(self) -> None:
        print_header("Update Student")
        lookup = prompt_string("Enter Student Code or ID to update")
        student = None
        if lookup.isdigit():
            student = self.student_service.get_by_id(int(lookup))
        if not student:
            student = self.student_service.get_by_code(lookup)

        if not student:
            print_error(f"Student '{lookup}' not found.")
            pause()
            return

        print_info(f"Updating Student: {student.full_name} ({student.student_code})")
        print_info("Leave blank to keep existing value.")

        new_first = prompt_string(f"First Name", default=student.first_name, required=False)
        new_last = prompt_string(f"Last Name", default=student.last_name, required=False)
        new_email = prompt_string(f"Email", default=student.email, required=False)
        new_phone = prompt_string(f"Phone", default=student.phone or "", required=False)
        new_status = prompt_choice("Status", ["Active", "Suspended", "Graduated", "Withdrawn"], default=student.status)

        updates = {
            "first_name": new_first,
            "last_name": new_last,
            "email": new_email,
            "phone": new_phone or None,
            "status": new_status,
        }

        try:
            self.student_service.update_student(student.student_id, updates)
            print_success(f"Student record '{student.student_code}' updated successfully.")
        except ValidationError as ve:
            print_error(f"Validation Error: {ve}")
        except Exception as e:
            print_error(f"Update failed: {e}")
        pause()

    def _action_delete_student(self) -> None:
        print_header("Delete Student")
        lookup = prompt_string("Enter Student Code or ID to delete")
        student = None
        if lookup.isdigit():
            student = self.student_service.get_by_id(int(lookup))
        if not student:
            student = self.student_service.get_by_code(lookup)

        if not student:
            print_error(f"Student '{lookup}' not found.")
            pause()
            return

        print_warning(
            f"Are you sure you want to delete {student.full_name} ({student.student_code})?"
        )
        print_warning("All associated enrollment and grade records will be permanently removed!")
        confirm = prompt_string("Type 'CONFIRM' to execute deletion")
        if confirm == "CONFIRM":
            try:
                self.student_service.delete_student(student.student_id)
                print_success(f"Student {student.student_code} successfully removed.")
            except Exception as e:
                print_error(f"Failed to delete student: {e}")
        else:
            print_info("Deletion cancelled.")
        pause()

    def _action_view_transcript(self) -> None:
        print_header("Student Official Transcript")
        lookup = prompt_string("Enter Student Code or ID")
        student = None
        if lookup.isdigit():
            student = self.student_service.get_by_id(int(lookup))
        if not student:
            student = self.student_service.get_by_code(lookup)

        if not student:
            print_error(f"Student '{lookup}' not found.")
            pause()
            return

        data = self.student_service.get_transcript(student.student_id)
        card_data = [
            ("Student Code", student.student_code),
            ("Full Name", student.full_name),
            ("Email", student.email),
            ("Status", student.status),
            ("Enrollment Date", student.enrollment_date),
            ("Cumulative GPA", f"{data['cumulative_gpa']:.2f} / 4.00"),
            ("Credits Attempted", data["total_credits_attempted"]),
            ("Credits Earned", data["total_credits_earned"]),
        ]
        print(format_card(card_data))

        courses = data["courses"]
        if not courses:
            print_warning("No academic coursework recorded for this student.")
        else:
            headers = ["Semester", "Course", "Title", "Credits", "Score", "Grade", "Points", "Status"]
            rows = [
                [
                    c["semester"],
                    c["course_code"],
                    c["course_name"],
                    c["credits"],
                    c["numeric_score"] if c["numeric_score"] is not None else "-",
                    c["letter_grade"] or "-",
                    f"{c['grade_point']:.2f}" if c["grade_point"] is not None else "-",
                    c["status"],
                ]
                for c in courses
            ]
            print(format_table(headers, rows, title="Course History & Grade Breakdown"))
        pause()

    # =========================================================================
    # 2. COURSE MANAGEMENT SUBMENU
    # =========================================================================
    def course_menu(self) -> None:
        while True:
            clear_screen()
            print_header("Course Management")
            print(f"  {BOLD}[1]{RESET} Add New Course")
            print(f"  {BOLD}[2]{RESET} View All Courses")
            print(f"  {BOLD}[3]{RESET} Search Course (by Code, Title, Department)")
            print(f"  {BOLD}[4]{RESET} Update Course Information")
            print(f"  {BOLD}[5]{RESET} Delete Course Record")
            print(f"  {BOLD}[6]{RESET} View Course Enrollment Roster")
            print(f"  {BOLD}[0]{RESET} Back to Main Menu")

            choice = prompt_string("Select option [0-6]")
            if choice == "1":
                self._action_add_course()
            elif choice == "2":
                self._action_view_all_courses()
            elif choice == "3":
                self._action_search_courses()
            elif choice == "4":
                self._action_update_course()
            elif choice == "5":
                self._action_delete_course()
            elif choice == "6":
                self._action_view_course_roster()
            elif choice == "0":
                break
            else:
                print_error("Invalid selection.")
                pause()

    def _action_add_course(self) -> None:
        print_header("Add New Course")
        try:
            code = prompt_string("Course Code (e.g. CS401)")
            name = prompt_string("Course Name")
            credits_val = prompt_int("Credit Units (1-6)", min_val=1, max_val=6, default=3)
            desc = prompt_string("Description (optional)", default="")
            dept = prompt_string("Department Code (e.g. CS, MATH, EE)", default="")
            capacity = prompt_int("Maximum Capacity", min_val=5, max_val=300, default=35)

            new_course = Course(
                course_code=code,
                course_name=name,
                credits=credits_val,
                description=desc or None,
                dept_code=dept or None,
                max_capacity=capacity,
            )
            course_id = self.course_service.create_course(new_course)
            print_success(f"Course '{new_course.course_code}' registered successfully (ID: {course_id}).")
        except ValidationError as ve:
            print_error(f"Validation failed: {ve}")
        except Exception as e:
            print_error(f"Failed to register course: {e}")
        pause()

    def _action_view_all_courses(self) -> None:
        print_header("Course Catalog")
        courses = self.course_service.list_all()
        if not courses:
            print_warning("No courses registered.")
        else:
            headers = ["ID", "Code", "Course Name", "Credits", "Department", "Max Cap"]
            rows = [
                [c.course_id, c.course_code, c.course_name, c.credits, c.dept_code or "-", c.max_capacity]
                for c in courses
            ]
            print(format_table(headers, rows, title=f"Active Courses ({len(courses)} total)"))
        pause()

    def _action_search_courses(self) -> None:
        print_header("Search Courses")
        term = prompt_string("Enter search term (Code, Name, or Department)")
        results = self.course_service.search(term)
        if not results:
            print_warning(f"No courses matching '{term}' found.")
        else:
            headers = ["Code", "Course Name", "Credits", "Department", "Capacity"]
            rows = [[c.course_code, c.course_name, c.credits, c.dept_code or "-", c.max_capacity] for c in results]
            print(format_table(headers, rows, title=f"Matching Courses ({len(results)} found)"))
        pause()

    def _action_update_course(self) -> None:
        print_header("Update Course")
        lookup = prompt_string("Enter Course Code or ID")
        course = None
        if lookup.isdigit():
            course = self.course_service.get_by_id(int(lookup))
        if not course:
            course = self.course_service.get_by_code(lookup)

        if not course:
            print_error(f"Course '{lookup}' not found.")
            pause()
            return

        print_info(f"Editing {course.course_code}: {course.course_name}")
        new_name = prompt_string("Course Name", default=course.course_name, required=False)
        new_credits = prompt_int("Credits (1-6)", min_val=1, max_val=6, default=course.credits)
        new_desc = prompt_string("Description", default=course.description or "", required=False)
        new_dept = prompt_string("Department Code", default=course.dept_code or "", required=False)
        new_cap = prompt_int("Capacity", min_val=1, max_val=500, default=course.max_capacity)

        updates = {
            "course_name": new_name,
            "credits": new_credits,
            "description": new_desc or None,
            "dept_code": new_dept or None,
            "max_capacity": new_cap,
        }

        try:
            self.course_service.update_course(course.course_id, updates)
            print_success(f"Course '{course.course_code}' updated successfully.")
        except ValidationError as ve:
            print_error(f"Validation error: {ve}")
        except Exception as e:
            print_error(f"Failed to update course: {e}")
        pause()

    def _action_delete_course(self) -> None:
        print_header("Delete Course")
        lookup = prompt_string("Enter Course Code or ID to delete")
        course = None
        if lookup.isdigit():
            course = self.course_service.get_by_id(int(lookup))
        if not course:
            course = self.course_service.get_by_code(lookup)

        if not course:
            print_error(f"Course '{lookup}' not found.")
            pause()
            return

        print_warning(f"Are you sure you want to remove {course.course_code} ({course.course_name})?")
        confirm = prompt_string("Type 'CONFIRM' to proceed")
        if confirm == "CONFIRM":
            try:
                self.course_service.delete_course(course.course_id)
                print_success(f"Course '{course.course_code}' deleted.")
            except Exception as e:
                print_error(f"Failed to delete course: {e}")
        else:
            print_info("Deletion cancelled.")
        pause()

    def _action_view_course_roster(self) -> None:
        print_header("Course Enrollment Roster")
        lookup = prompt_string("Enter Course Code or ID")
        course = None
        if lookup.isdigit():
            course = self.course_service.get_by_id(int(lookup))
        if not course:
            course = self.course_service.get_by_code(lookup)

        if not course:
            print_error(f"Course '{lookup}' not found.")
            pause()
            return

        semester = prompt_string("Filter by Semester (e.g. Fall 2025, or leave blank for all)", default="")
        roster = self.course_service.get_roster(course.course_id, semester or None)

        if not roster:
            print_warning(f"No students currently enrolled in {course.course_code}.")
        else:
            headers = ["Student ID", "Code", "Student Name", "Email", "Semester", "Score", "Grade", "Status"]
            rows = [
                [
                    r["student_id"],
                    r["student_code"],
                    f"{r['first_name']} {r['last_name']}",
                    r["email"],
                    r["semester"],
                    r["numeric_score"] if r["numeric_score"] is not None else "-",
                    r["letter_grade"] or "-",
                    r["status"],
                ]
                for r in roster
            ]
            print(format_table(headers, rows, title=f"Roster for {course.course_code} ({len(roster)} enrolled)"))
        pause()

    # =========================================================================
    # 3. GRADES & ENROLLMENT SUBMENU
    # =========================================================================
    def grade_menu(self) -> None:
        while True:
            clear_screen()
            print_header("Grades & Enrollment Management")
            print(f"  {BOLD}[1]{RESET} Enroll Student in Course")
            print(f"  {BOLD}[2]{RESET} Record / Update Student Grade")
            print(f"  {BOLD}[3]{RESET} View All Enrollments & Grades")
            print(f"  {BOLD}[4]{RESET} Drop Student from Course")
            print(f"  {BOLD}[5]{RESET} View Course Grade Performance & Statistics")
            print(f"  {BOLD}[0]{RESET} Back to Main Menu")

            choice = prompt_string("Select option [0-5]")
            if choice == "1":
                self._action_enroll_student()
            elif choice == "2":
                self._action_record_grade()
            elif choice == "3":
                self._action_view_enrollments()
            elif choice == "4":
                self._action_drop_course()
            elif choice == "5":
                self._action_course_statistics()
            elif choice == "0":
                break
            else:
                print_error("Invalid selection.")
                pause()

    def _action_enroll_student(self) -> None:
        print_header("Enroll Student in Course")
        try:
            stu_lookup = prompt_string("Enter Student Code or ID")
            student = self.student_service.get_by_id(int(stu_lookup)) if stu_lookup.isdigit() else self.student_service.get_by_code(stu_lookup)
            if not student:
                raise ValidationError(f"Student '{stu_lookup}' not found.")

            crs_lookup = prompt_string("Enter Course Code or ID")
            course = self.course_service.get_by_id(int(crs_lookup)) if crs_lookup.isdigit() else self.course_service.get_by_code(crs_lookup)
            if not course:
                raise ValidationError(f"Course '{crs_lookup}' not found.")

            semester = prompt_string("Academic Semester (e.g. Fall 2026)")

            enrollment_id = self.grade_service.enroll_student(student.student_id, course.course_id, semester)
            print_success(
                f"Student {student.full_name} enrolled in {course.course_code} ({course.course_name}) for {semester} [Enrollment ID: {enrollment_id}]."
            )
        except ValidationError as ve:
            print_error(f"Enrollment rejected: {ve}")
        except Exception as e:
            print_error(f"Enrollment failed: {e}")
        pause()

    def _action_record_grade(self) -> None:
        print_header("Record / Update Grade")
        try:
            lookup = prompt_string("Enter Enrollment ID (or press Enter to search by student)", default="")
            enrollment = None
            if lookup.isdigit():
                enrollment = self.grade_service.get_by_id(int(lookup))

            if not enrollment:
                stu_code = prompt_string("Enter Student Code")
                student = self.student_service.get_by_code(stu_code)
                if not student:
                    raise ValidationError(f"Student '{stu_code}' not found.")

                enrollments = self.grade_service.list_enrollments(student_id=student.student_id)
                if not enrollments:
                    raise ValidationError(f"Student {student.full_name} has no enrollments.")

                headers = ["Enroll ID", "Course", "Semester", "Score", "Grade", "Status"]
                rows = [
                    [e["enrollment_id"], e["course_code"], e["semester"], e["numeric_score"] or "-", e["letter_grade"] or "-", e["status"]]
                    for e in enrollments
                ]
                print(format_table(headers, rows, title=f"Active Enrollments for {student.full_name}"))
                chosen_id = prompt_int("Enter Enrollment ID to grade")
                enrollment = self.grade_service.get_by_id(chosen_id)

            if not enrollment:
                raise ValidationError("Enrollment not found.")

            print_info(
                f"Grading: {enrollment['first_name']} {enrollment['last_name']} in {enrollment['course_code']} ({enrollment['semester']})"
            )
            score = prompt_float("Enter Numeric Score (0.0 to 100.0)", min_val=0.0, max_val=100.0)
            self.grade_service.record_grade(enrollment["enrollment_id"], score)
            updated = self.grade_service.get_by_id(enrollment["enrollment_id"])
            print_success(
                f"Grade updated: Score: {updated['numeric_score']} | Letter Grade: {updated['letter_grade']} | GPA Points: {updated['grade_point']}."
            )
        except ValidationError as ve:
            print_error(f"Grade validation failed: {ve}")
        except Exception as e:
            print_error(f"Failed to record grade: {e}")
        pause()

    def _action_view_enrollments(self) -> None:
        print_header("Enrollment & Grade Directory")
        sem_filter = prompt_string("Filter by Semester (leave blank for all)", default="")
        enrollments = self.grade_service.list_enrollments(semester=sem_filter or None)

        if not enrollments:
            print_warning("No enrollments matching the criteria.")
        else:
            headers = ["ID", "Student Code", "Student Name", "Course", "Credits", "Semester", "Score", "Grade", "Points", "Status"]
            rows = [
                [
                    e["enrollment_id"],
                    e["student_code"],
                    e["student_name"],
                    e["course_code"],
                    e["credits"],
                    e["semester"],
                    e["numeric_score"] if e["numeric_score"] is not None else "-",
                    e["letter_grade"] or "-",
                    f"{e['grade_point']:.2f}" if e["grade_point"] is not None else "-",
                    e["status"],
                ]
                for e in enrollments
            ]
            print(format_table(headers, rows, title=f"Enrollment Records ({len(enrollments)} records)"))
        pause()

    def _action_drop_course(self) -> None:
        print_header("Drop Student from Course")
        try:
            enroll_id = prompt_int("Enter Enrollment ID to drop")
            enrollment = self.grade_service.get_by_id(enroll_id)
            if not enrollment:
                raise ValidationError(f"Enrollment ID {enroll_id} does not exist.")

            print_warning(
                f"Drop {enrollment['student_code']} from {enrollment['course_code']} ({enrollment['semester']})?"
            )
            confirm = prompt_string("Type 'DROP' to confirm")
            if confirm == "DROP":
                self.grade_service.drop_course(enroll_id)
                print_success("Course successfully dropped (Status set to 'Dropped', Grade marked 'W').")
            else:
                print_info("Operation cancelled.")
        except ValidationError as ve:
            print_error(f"Error: {ve}")
        except Exception as e:
            print_error(f"Drop operation failed: {e}")
        pause()

    def _action_course_statistics(self) -> None:
        print_header("Course Academic Statistics")
        lookup = prompt_string("Enter Course Code or ID")
        course = self.course_service.get_by_id(int(lookup)) if lookup.isdigit() else self.course_service.get_by_code(lookup)
        if not course:
            print_error(f"Course '{lookup}' not found.")
            pause()
            return

        semester = prompt_string("Semester filter (or leave blank for all)", default="")
        stats = self.grade_service.get_course_stats(course.course_id, semester or None)

        card_data = [
            ("Course Code", course.course_code),
            ("Course Name", course.course_name),
            ("Semester", stats["semester"]),
            ("Graded Students", stats["count"]),
            ("Average Score", f"{stats['average_score']}%" if stats["average_score"] is not None else "N/A"),
            ("Highest Score", f"{stats['highest_score']}%" if stats["highest_score"] is not None else "N/A"),
            ("Lowest Score", f"{stats['lowest_score']}%" if stats["lowest_score"] is not None else "N/A"),
            ("Pass Rate", f"{stats['pass_rate']}%" if stats["pass_rate"] is not None else "N/A"),
        ]
        print(format_card(card_data))

        dist = stats["grade_distribution"]
        if dist:
            dist_rows = [[grade, count] for grade, count in sorted(dist.items())]
            print(format_table(["Grade", "Count"], dist_rows, title="Letter Grade Distribution"))
        pause()

    # =========================================================================
    # 4. REPORTS & ANALYTICS SUBMENU
    # =========================================================================
    def reports_menu(self) -> None:
        while True:
            clear_screen()
            print_header("Reports & Analytics")
            print(f"  {BOLD}[1]{RESET} Honor Roll / Dean's List (Top Cumulative GPA)")
            print(f"  {BOLD}[2]{RESET} Department Enrollment & Performance Summary")
            print(f"  {BOLD}[3]{RESET} Institutional Grade Distribution")
            print(f"  {BOLD}[4]{RESET} Export Student Roster to CSV")
            print(f"  {BOLD}[5]{RESET} Export All Grades & Transcripts to CSV")
            print(f"  {BOLD}[6]{RESET} Export Complete Database Snapshot to JSON")
            print(f"  {BOLD}[0]{RESET} Back to Main Menu")

            choice = prompt_string("Select option [0-6]")
            if choice == "1":
                self._action_report_honor_roll()
            elif choice == "2":
                self._action_report_departments()
            elif choice == "3":
                self._action_report_grade_dist()
            elif choice == "4":
                self._action_export_students()
            elif choice == "5":
                self._action_export_grades()
            elif choice == "6":
                self._action_export_json()
            elif choice == "0":
                break
            else:
                print_error("Invalid selection.")
                pause()

    def _action_report_honor_roll(self) -> None:
        print_header("Dean's Honor Roll")
        min_gpa = prompt_float("Minimum GPA Threshold (default 3.5)", min_val=0.0, max_val=4.0, default=3.5)
        min_credits = prompt_int("Minimum Credits Completed", min_val=1, default=3)

        honors = self.report_service.get_honor_roll(min_gpa=min_gpa, min_credits=min_credits)
        if not honors:
            print_warning(f"No students found with GPA >= {min_gpa} and credits >= {min_credits}.")
        else:
            headers = ["Rank", "Code", "Student Name", "Email", "Earned Credits", "Cumulative GPA"]
            rows = [
                [
                    idx,
                    h["student_code"],
                    h["student_name"],
                    h["email"],
                    h["credits_earned"],
                    f"{h['cumulative_gpa']:.2f}",
                ]
                for idx, h in enumerate(honors, 1)
            ]
            print(format_table(headers, rows, title=f"Dean's Honor List (GPA >= {min_gpa})"))
        pause()

    def _action_report_departments(self) -> None:
        print_header("Departmental Academic Summary")
        summary = self.report_service.get_department_summary()
        headers = ["Code", "Department Name", "Courses", "Enrollments", "Avg Score"]
        rows = [
            [d["dept_code"], d["dept_name"], d["total_courses"], d["total_enrollments"], f"{d['avg_score']}%"]
            for d in summary
        ]
        print(format_table(headers, rows, title="Department Performance Overview"))
        pause()

    def _action_report_grade_dist(self) -> None:
        print_header("Institutional Grade Distribution")
        dist = self.report_service.get_overall_grade_distribution()
        if not dist:
            print_warning("No graded enrollments available.")
        else:
            headers = ["Letter Grade", "Total Count", "Share (%)"]
            rows = [[d["letter_grade"], d["count"], f"{d['percentage']}%"] for d in dist]
            print(format_table(headers, rows, title="All-Courses Grade Breakdown"))
        pause()

    def _action_export_students(self) -> None:
        print_header("Export Students to CSV")
        try:
            path = self.report_service.export_students_csv()
            print_success(f"Student records exported successfully to: {path}")
        except Exception as e:
            print_error(f"Export failed: {e}")
        pause()

    def _action_export_grades(self) -> None:
        print_header("Export Grades to CSV")
        try:
            path = self.report_service.export_grades_csv()
            print_success(f"Enrollments and grades exported successfully to: {path}")
        except Exception as e:
            print_error(f"Export failed: {e}")
        pause()

    def _action_export_json(self) -> None:
        print_header("Export Database JSON Snapshot")
        try:
            path = self.report_service.export_database_json()
            print_success(f"Full database JSON snapshot created at: {path}")
        except Exception as e:
            print_error(f"JSON export failed: {e}")
        pause()

    # =========================================================================
    # 5. SYSTEM & DATABASE UTILITIES
    # =========================================================================
    def system_menu(self) -> None:
        while True:
            clear_screen()
            print_header("Database & System Utilities")
            print(f"  {BOLD}[1]{RESET} View Database Engine & Statistics")
            print(f"  {BOLD}[2]{RESET} Populate Database with Sample Demo Data")
            print(f"  {BOLD}[3]{RESET} Switch Active Database Engine (SQLite / MySQL)")
            print(f"  {BOLD}[4]{RESET} Run Database Integrity & Health Check")
            print(f"  {BOLD}[0]{RESET} Back to Main Menu")

            choice = prompt_string("Select option [0-4]")
            if choice == "1":
                self._action_system_status()
            elif choice == "2":
                self._action_seed_data()
            elif choice == "3":
                self._action_switch_engine()
            elif choice == "4":
                self._action_integrity_check()
            elif choice == "0":
                break
            else:
                print_error("Invalid selection.")
                pause()

    def _action_system_status(self) -> None:
        print_header("System & Database Diagnostics")
        try:
            stu_count = self.db.fetch_one("SELECT COUNT(*) AS c FROM students")["c"]
            crs_count = self.db.fetch_one("SELECT COUNT(*) AS c FROM courses")["c"]
            enr_count = self.db.fetch_one("SELECT COUNT(*) AS c FROM enrollments")["c"]
            dpt_count = self.db.fetch_one("SELECT COUNT(*) AS c FROM departments")["c"]

            card_info = [
                ("Application", config.APP_NAME),
                ("Version", config.APP_VERSION),
                ("Database Engine", config.DB_ENGINE.upper()),
                ("Storage Target", config.SQLITE_DB_PATH if config.DB_ENGINE == "sqlite" else f"{config.MYSQL_CONFIG['user']}@{config.MYSQL_CONFIG['host']}:{config.MYSQL_CONFIG['port']}/{config.MYSQL_CONFIG['database']}"),
                ("Total Departments", dpt_count),
                ("Total Students", stu_count),
                ("Total Courses", crs_count),
                ("Total Enrollments", enr_count),
            ]
            print(format_card(card_info))
        except Exception as e:
            print_error(f"Failed to query system status: {e}")
        pause()

    def _action_seed_data(self) -> None:
        print_header("Seed Sample Data")
        print_info("This will populate realistic sample departments, students, courses, and graded enrollments.")
        reset_choice = prompt_choice("Reset existing data or keep?", ["Keep existing (Insert new)", "Reset all and repopulate", "Cancel"], default="Keep existing (Insert new)")

        if reset_choice == "Cancel":
            return

        should_reset = "Reset all" in reset_choice
        try:
            seed_database(self.db, reset=should_reset)
            print_success("Database successfully loaded with sample records.")
        except Exception as e:
            print_error(f"Seeding failed: {e}")
        pause()

    def _action_switch_engine(self) -> None:
        print_header("Switch Database Engine")
        print_info(f"Current Engine: {config.DB_ENGINE.upper()}")
        new_engine = prompt_choice("Select Target Engine:", ["SQLite", "MySQL", "Cancel"], default="SQLite")

        if new_engine == "Cancel":
            return

        target = new_engine.lower()
        if target == "mysql":
            print_info("Testing PyMySQL dependency and MySQL connection parameters...")
            try:
                import pymysql
                test_mgr = DatabaseManager(engine="mysql")
                test_conn = test_mgr.get_connection()
                test_conn.close()
                config.DB_ENGINE = "mysql"
                self.db = test_mgr
                print_success("Connected to MySQL database successfully!")
            except ImportError:
                print_error("PyMySQL is not installed. Run 'pip install pymysql' to use MySQL.")
            except Exception as e:
                print_error(f"Failed to connect to MySQL: {e}")
                print_warning("Check config.py or set environment variables SRMS_MYSQL_HOST, SRMS_MYSQL_USER, etc.")
        else:
            config.DB_ENGINE = "sqlite"
            self.db = DatabaseManager(engine="sqlite")
            self.db.initialize_schema()
            print_success("Switched to SQLite database successfully.")
        pause()

    def _action_integrity_check(self) -> None:
        print_header("Database Integrity & Foreign Key Check")
        try:
            if config.DB_ENGINE == "sqlite":
                conn = self.db.get_connection()
                check_result = conn.execute("PRAGMA integrity_check;").fetchall()
                fk_check = conn.execute("PRAGMA foreign_key_check;").fetchall()
                conn.close()

                print_success(f"SQLite Integrity Check: {[r[0] for r in check_result]}")
                if not fk_check:
                    print_success("Foreign Key Consistency: OK (No violations found).")
                else:
                    print_warning(f"Foreign Key violations found: {fk_check}")
            else:
                print_success("MySQL Foreign Key constraints enforced via InnoDB storage engine.")
        except Exception as e:
            print_error(f"Integrity check failed: {e}")
        pause()
