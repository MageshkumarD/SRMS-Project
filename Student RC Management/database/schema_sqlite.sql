-- =============================================================================
-- SQLite Schema: Student Records Management System
-- Normalization: 3NF with Foreign Key Constraints & Data Integrity Checks
-- =============================================================================

PRAGMA foreign_keys = ON;

-- 1. Departments Table
CREATE TABLE IF NOT EXISTS departments (
    dept_id INTEGER PRIMARY KEY AUTOINCREMENT,
    dept_code TEXT UNIQUE NOT NULL,
    dept_name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Students Table
CREATE TABLE IF NOT EXISTS students (
    student_id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_code TEXT UNIQUE NOT NULL,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    phone TEXT,
    date_of_birth DATE NOT NULL,
    enrollment_date DATE NOT NULL,
    status TEXT NOT NULL DEFAULT 'Active' CHECK(status IN ('Active', 'Suspended', 'Graduated', 'Withdrawn')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Courses Table
CREATE TABLE IF NOT EXISTS courses (
    course_id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_code TEXT UNIQUE NOT NULL,
    course_name TEXT NOT NULL,
    description TEXT,
    credits INTEGER NOT NULL CHECK(credits >= 1 AND credits <= 6),
    dept_code TEXT,
    max_capacity INTEGER NOT NULL DEFAULT 40 CHECK(max_capacity > 0),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (dept_code) REFERENCES departments(dept_code) ON UPDATE CASCADE ON DELETE SET NULL
);

-- 4. Enrollments & Grades Table
CREATE TABLE IF NOT EXISTS enrollments (
    enrollment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    course_id INTEGER NOT NULL,
    semester TEXT NOT NULL,
    numeric_score REAL CHECK(numeric_score IS NULL OR (numeric_score >= 0.0 AND numeric_score <= 100.0)),
    letter_grade TEXT CHECK(letter_grade IS NULL OR letter_grade IN ('A+', 'A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'C-', 'D', 'F', 'W', 'I')),
    grade_point REAL CHECK(grade_point IS NULL OR (grade_point >= 0.0 AND grade_point <= 4.0)),
    status TEXT NOT NULL DEFAULT 'Enrolled' CHECK(status IN ('Enrolled', 'Completed', 'Dropped')),
    enrollment_date DATE NOT NULL,
    grade_date DATE,
    FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
    FOREIGN KEY (course_id) REFERENCES courses(course_id) ON DELETE CASCADE,
    UNIQUE(student_id, course_id, semester)
);

-- Indexes for optimal lookup performance
CREATE INDEX IF NOT EXISTS idx_students_code ON students(student_code);
CREATE INDEX IF NOT EXISTS idx_students_email ON students(email);
CREATE INDEX IF NOT EXISTS idx_students_name ON students(last_name, first_name);
CREATE INDEX IF NOT EXISTS idx_courses_code ON courses(course_code);
CREATE INDEX IF NOT EXISTS idx_enrollments_student ON enrollments(student_id);
CREATE INDEX IF NOT EXISTS idx_enrollments_course ON enrollments(course_id);
CREATE INDEX IF NOT EXISTS idx_enrollments_semester ON enrollments(semester);
