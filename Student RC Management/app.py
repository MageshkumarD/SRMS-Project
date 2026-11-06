"""
Interactive Web Application for Student Records Management System (SRMS).
Built with Flask, TailwindCSS, Chart.js, and the SRMS Relational Engine.
Provides a modern, reactive browser dashboard alongside the CLI.
"""

import os
import sys
import webbrowser
from threading import Timer
from flask import Flask, render_template, request, jsonify, send_file

import config
from database.connection import db, DatabaseManager
from database.seed_data import seed_database
from models.student import Student
from models.course import Course
from services.student_service import StudentService
from services.course_service import CourseService
from services.grade_service import GradeService
from services.report_service import ReportService
from utils.validators import ValidationError

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Initialize Services
student_service = StudentService(db)
course_service = CourseService(db)
grade_service = GradeService(db)
report_service = ReportService(db)

# Ensure database schema is ready
db.initialize_schema()


# =============================================================================
# CONTEXT PROCESSOR (Inject Global Variables into Templates)
# =============================================================================
@app.context_processor
def inject_globals():
    return {
        "db_engine": config.DB_ENGINE,
        "app_name": config.APP_NAME,
        "app_version": config.APP_VERSION,
    }


# =============================================================================
# HTML PAGE ROUTES
# =============================================================================
@app.route("/")
def dashboard():
    stu_count = db.fetch_one("SELECT COUNT(*) AS c FROM students")["c"]
    crs_count = db.fetch_one("SELECT COUNT(*) AS c FROM courses")["c"]
    enr_count = db.fetch_one("SELECT COUNT(*) AS c FROM enrollments")["c"]
    dpt_count = db.fetch_one("SELECT COUNT(*) AS c FROM departments")["c"]

    # Calculate Institutional Average GPA
    avg_row = db.fetch_one(
        """
        SELECT ROUND(AVG(grade_point), 2) AS avg_gpa 
        FROM enrollments 
        WHERE grade_point IS NOT NULL AND status = 'Completed'
        """
    )
    avg_gpa = avg_row["avg_gpa"] if (avg_row and avg_row["avg_gpa"] is not None) else 0.00

    grade_distribution = report_service.get_overall_grade_distribution()
    department_summary = report_service.get_department_summary()
    top_students = report_service.get_honor_roll(min_gpa=3.5, min_credits=3, limit=5)

    return render_template(
        "dashboard.html",
        active_page="dashboard",
        total_students=stu_count,
        total_courses=crs_count,
        total_enrollments=enr_count,
        total_departments=dpt_count,
        avg_gpa=f"{avg_gpa:.2f}",
        grade_distribution=grade_distribution,
        department_summary=department_summary,
        top_students=top_students,
    )


@app.route("/students")
def students_page():
    students = student_service.list_all(limit=500)
    return render_template(
        "students.html",
        active_page="students",
        students=students,
    )


@app.route("/courses")
def courses_page():
    courses = course_service.list_all(limit=500)
    return render_template(
        "courses.html",
        active_page="courses",
        courses=courses,
    )


@app.route("/grades")
def grades_page():
    enrollments = grade_service.list_enrollments()
    students = student_service.list_all(status="Active")
    courses = course_service.list_all()

    semesters = sorted(list({e["semester"] for e in enrollments if e.get("semester")}))

    return render_template(
        "grades.html",
        active_page="grades",
        enrollments=enrollments,
        students=students,
        courses=courses,
        semesters=semesters,
    )


@app.route("/reports")
def reports_page():
    honors = report_service.get_honor_roll(min_gpa=3.0, min_credits=1, limit=50)
    departments = report_service.get_department_summary()
    return render_template(
        "reports.html",
        active_page="reports",
        honors=honors,
        departments=departments,
    )


# =============================================================================
# REST API ENDPOINTS
# =============================================================================
@app.route("/api/students", methods=["GET", "POST"])
def api_students():
    if request.method == "POST":
        data = request.get_json() or {}
        try:
            student = Student(
                student_code=data.get("student_code", ""),
                first_name=data.get("first_name", ""),
                last_name=data.get("last_name", ""),
                email=data.get("email", ""),
                phone=data.get("phone") or None,
                date_of_birth=data.get("date_of_birth", ""),
                enrollment_date=data.get("enrollment_date", ""),
                status=data.get("status", "Active"),
            )
            s_id = student_service.create_student(student)
            return jsonify({"success": True, "student_id": s_id, "message": "Student created successfully!"})
        except ValidationError as ve:
            return jsonify({"success": False, "error": str(ve)}), 400
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    students = [s.to_dict() for s in student_service.list_all()]
    return jsonify({"success": True, "students": students})


@app.route("/api/students/<int:student_id>", methods=["GET", "PUT", "DELETE"])
def api_student_detail(student_id):
    if request.method == "GET":
        student = student_service.get_by_id(student_id)
        if not student:
            return jsonify({"success": False, "error": "Student not found"}), 404
        return jsonify({"success": True, "student": student.to_dict()})

    elif request.method == "PUT":
        data = request.get_json() or {}
        try:
            student_service.update_student(student_id, data)
            return jsonify({"success": True, "message": "Student updated successfully!"})
        except ValidationError as ve:
            return jsonify({"success": False, "error": str(ve)}), 400
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    elif request.method == "DELETE":
        try:
            student_service.delete_student(student_id)
            return jsonify({"success": True, "message": "Student deleted successfully!"})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/students/<int:student_id>/transcript", methods=["GET"])
def api_student_transcript(student_id):
    try:
        transcript = student_service.get_transcript(student_id)
        transcript["student"] = transcript["student"].to_dict()
        return jsonify({"success": True, **transcript})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 404


@app.route("/api/courses", methods=["GET", "POST"])
def api_courses():
    if request.method == "POST":
        data = request.get_json() or {}
        try:
            course = Course(
                course_code=data.get("course_code", ""),
                course_name=data.get("course_name", ""),
                credits=int(data.get("credits", 3)),
                dept_code=data.get("dept_code") or None,
                max_capacity=int(data.get("max_capacity", 35)),
                description=data.get("description") or None,
            )
            c_id = course_service.create_course(course)
            return jsonify({"success": True, "course_id": c_id, "message": "Course registered successfully!"})
        except ValidationError as ve:
            return jsonify({"success": False, "error": str(ve)}), 400
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    courses = [c.to_dict() for c in course_service.list_all()]
    return jsonify({"success": True, "courses": courses})


@app.route("/api/courses/<int:course_id>", methods=["GET", "PUT", "DELETE"])
def api_course_detail(course_id):
    if request.method == "GET":
        course = course_service.get_by_id(course_id)
        if not course:
            return jsonify({"success": False, "error": "Course not found"}), 404
        return jsonify({"success": True, "course": course.to_dict()})

    elif request.method == "PUT":
        data = request.get_json() or {}
        try:
            course_service.update_course(course_id, data)
            return jsonify({"success": True, "message": "Course updated successfully!"})
        except ValidationError as ve:
            return jsonify({"success": False, "error": str(ve)}), 400
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    elif request.method == "DELETE":
        try:
            course_service.delete_course(course_id)
            return jsonify({"success": True, "message": "Course deleted successfully!"})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/courses/<int:course_id>/roster", methods=["GET"])
def api_course_roster(course_id):
    try:
        roster = course_service.get_roster(course_id)
        return jsonify({"success": True, "roster": roster})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/enrollments", methods=["POST"])
def api_enroll_student():
    data = request.get_json() or {}
    try:
        s_id = int(data.get("student_id"))
        c_id = int(data.get("course_id"))
        sem = data.get("semester", "")
        e_id = grade_service.enroll_student(s_id, c_id, sem)
        return jsonify({"success": True, "enrollment_id": e_id, "message": "Student enrolled successfully!"})
    except ValidationError as ve:
        return jsonify({"success": False, "error": str(ve)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/enrollments/<int:enrollment_id>/grade", methods=["POST"])
def api_record_grade(enrollment_id):
    data = request.get_json() or {}
    try:
        score = float(data.get("score"))
        grade_service.record_grade(enrollment_id, score)
        return jsonify({"success": True, "message": "Grade recorded successfully!"})
    except ValidationError as ve:
        return jsonify({"success": False, "error": str(ve)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/enrollments/<int:enrollment_id>/drop", methods=["POST"])
def api_drop_course(enrollment_id):
    try:
        grade_service.drop_course(enrollment_id)
        return jsonify({"success": True, "message": "Course marked as dropped (Withdrawn)."})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/seed", methods=["POST"])
def api_seed_database():
    try:
        seed_database(db, reset=False)
        return jsonify({"success": True, "message": "Sample academic records seeded successfully!"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# =============================================================================
# FILE EXPORT ENDPOINTS
# =============================================================================
@app.route("/export/students.csv")
def download_students_csv():
    filepath = report_service.export_students_csv()
    return send_file(filepath, as_attachment=True, mimetype="text/csv", download_name="students_export.csv")


@app.route("/export/grades.csv")
def download_grades_csv():
    filepath = report_service.export_grades_csv()
    return send_file(filepath, as_attachment=True, mimetype="text/csv", download_name="grades_export.csv")


@app.route("/export/backup.json")
def download_backup_json():
    filepath = report_service.export_database_json()
    return send_file(filepath, as_attachment=True, download_name="database_backup.json")


# =============================================================================
# APP RUNNER
# =============================================================================
def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000")


def run_web(open_tab: bool = True, port: int = 5000):
    if open_tab:
        Timer(1.2, open_browser).start()
    print(f"\n🌐 Starting SRMS Interactive Web Dashboard at http://127.0.0.1:{port} ...")
    print("👉 Press Ctrl+C in this terminal to stop the web server.\n")
    app.run(host="127.0.0.1", port=port, debug=False)


if __name__ == "__main__":
    run_web()
