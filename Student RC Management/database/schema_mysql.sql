-- =============================================================================
-- MySQL Schema: Student Records Management System
-- Normalization: 3NF with Foreign Key Constraints & Data Integrity Checks
-- Storage Engine: InnoDB (Full ACID compliance & Foreign Key enforcement)
-- =============================================================================

CREATE DATABASE IF NOT EXISTS student_records_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE student_records_db;

-- 1. Departments Table
CREATE TABLE IF NOT EXISTS departments (
    dept_id INT AUTO_INCREMENT PRIMARY KEY,
    dept_code VARCHAR(10) UNIQUE NOT NULL,
    dept_name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- 2. Students Table
CREATE TABLE IF NOT EXISTS students (
    student_id INT AUTO_INCREMENT PRIMARY KEY,
    student_code VARCHAR(20) UNIQUE NOT NULL,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(25),
    date_of_birth DATE NOT NULL,
    enrollment_date DATE NOT NULL,
    status ENUM('Active', 'Suspended', 'Graduated', 'Withdrawn') NOT NULL DEFAULT 'Active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_students_code (student_code),
    INDEX idx_students_email (email),
    INDEX idx_students_name (last_name, first_name)
) ENGINE=InnoDB;

-- 3. Courses Table
CREATE TABLE IF NOT EXISTS courses (
    course_id INT AUTO_INCREMENT PRIMARY KEY,
    course_code VARCHAR(20) UNIQUE NOT NULL,
    course_name VARCHAR(100) NOT NULL,
    description TEXT,
    credits INT NOT NULL,
    dept_code VARCHAR(10),
    max_capacity INT NOT NULL DEFAULT 40,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_credits CHECK (credits >= 1 AND credits <= 6),
    CONSTRAINT chk_capacity CHECK (max_capacity > 0),
    CONSTRAINT fk_courses_dept FOREIGN KEY (dept_code) REFERENCES departments(dept_code) ON UPDATE CASCADE ON DELETE SET NULL,
    INDEX idx_courses_code (course_code)
) ENGINE=InnoDB;

-- 4. Enrollments & Grades Table
CREATE TABLE IF NOT EXISTS enrollments (
    enrollment_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    course_id INT NOT NULL,
    semester VARCHAR(20) NOT NULL,
    numeric_score DECIMAL(5, 2) NULL,
    letter_grade VARCHAR(2) NULL,
    grade_point DECIMAL(3, 2) NULL,
    status ENUM('Enrolled', 'Completed', 'Dropped') NOT NULL DEFAULT 'Enrolled',
    enrollment_date DATE NOT NULL,
    grade_date DATE NULL,
    CONSTRAINT chk_score CHECK (numeric_score IS NULL OR (numeric_score >= 0.0 AND numeric_score <= 100.0)),
    CONSTRAINT chk_grade CHECK (letter_grade IS NULL OR letter_grade IN ('A+', 'A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'C-', 'D', 'F', 'W', 'I')),
    CONSTRAINT chk_gpa CHECK (grade_point IS NULL OR (grade_point >= 0.0 AND grade_point <= 4.0)),
    CONSTRAINT fk_enrollments_student FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
    CONSTRAINT fk_enrollments_course FOREIGN KEY (course_id) REFERENCES courses(course_id) ON DELETE CASCADE,
    CONSTRAINT uq_student_course_sem UNIQUE (student_id, course_id, semester),
    INDEX idx_enrollments_student (student_id),
    INDEX idx_enrollments_course (course_id),
    INDEX idx_enrollments_sem (semester)
) ENGINE=InnoDB;
