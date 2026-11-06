# 🎓 Student Records Management System (SRMS)

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Database](https://img.shields.io/badge/database-SQLite%20%7C%20MySQL-orange.svg)](https://www.sqlite.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Security: Parameterized SQL](https://img.shields.io/badge/security-100%25%20Parameterized%20Queries-brightgreen.svg)](#security--sql-injection-prevention)

A normalized, production-grade **Student Records Management System** built with **Python**, **SQL**, **SQLite**, and **MySQL**. It features an enterprise data model in 3rd Normal Form (3NF), full **CRUD** operations for students, courses, and graded enrollments, strict input validation and transaction controls, and an interactive menu-driven terminal interface.

---

## 🌟 Key Features

* **Complete CRUD Engine**: End-to-end Create, Read, Update, and Delete operations for Student, Course, and Grade/Enrollment entities.
* **SQL Injection Immune**: 100% parameterized queries across all database drivers. No user input is ever concatenated into raw SQL strings.
* **Normalized 3NF Architecture**: Comprehensive relational schema with foreign key constraints, `ON DELETE CASCADE`, unique indexes, and domain check constraints.
* **Dual Database Backend**:
  * **SQLite** (Default): Zero-setup, self-contained serverless storage.
  * **MySQL**: Production-ready InnoDB cluster configuration with seamless driver switching.
* **Input Validation & Business Rules**: RFC-compliant email verification, age limits, date chronologies, course credit hour boundaries (1-6), and automated GPA calculation (4.0 scale).
* **Interactive Menu-Driven CLI**: Styled terminal interface with ASCII borders, status indicators, student transcripts, and reports.
* **Academic Analytics & Data Export**: Dean's Honor Roll calculation, departmental summaries, pass/fail rates, and 1-click export to **CSV** and **JSON**.

---

## 🏗️ Architecture & Component Design

```mermaid
graph TD
    UI[🖥️ CLI Menu Handler / UI Layer]
    VAL[🛡️ Input Validators & Sanitization]
    
    subgraph Services [Business Logic & Service Layer]
        SS[Student Service]
        CS[Course Service]
        GS[Grade & Enrollment Service]
        RS[Reporting & Export Service]
    end

    subgraph Data [Data Access & Abstraction Layer]
        DBM[Database Manager & Query Adapter]
        SQLITE[(SQLite Database\ndata/student_records.db)]
        MYSQL[(MySQL Database\nInnoDB Engine)]
    end

    UI --> VAL
    VAL --> Services
    Services --> DBM
    DBM --> SQLITE
    DBM --> MYSQL
```

---

## 🗄️ Relational Database Schema (3NF)

```mermaid
erDiagram
    DEPARTMENTS ||--o{ COURSES : "offers"
    STUDENTS ||--o{ ENROLLMENTS : "registers"
    COURSES ||--o{ ENROLLMENTS : "has"

    DEPARTMENTS {
        int dept_id PK
        string dept_code UK
        string dept_name
        timestamp created_at
    }

    STUDENTS {
        int student_id PK
        string student_code UK
        string first_name
        string last_name
        string email UK
        string phone
        date date_of_birth
        date enrollment_date
        string status "Active | Suspended | Graduated | Withdrawn"
        timestamp created_at
        timestamp updated_at
    }

    COURSES {
        int course_id PK
        string course_code UK
        string course_name
        text description
        int credits "1 to 6"
        string dept_code FK
        int max_capacity
        timestamp created_at
    }

    ENROLLMENTS {
        int enrollment_id PK
        int student_id FK
        int course_id FK
        string semester "e.g. Fall 2026"
        float numeric_score "0.00 to 100.00"
        string letter_grade "A+, A, B, C, D, F, W, I"
        float grade_point "0.00 to 4.00"
        string status "Enrolled | Completed | Dropped"
        date enrollment_date
        date grade_date
    }
```

---

## 🔒 Security & SQL Injection Prevention

All database interactions use **parameterized placeholders** (`?` for SQLite, translated dynamically to `%s` for MySQL via `DatabaseManager`). User input is passed exclusively as discrete bound parameters:

```python
# SECURE: Safe parameterized query execution
query = """
    SELECT * FROM students 
    WHERE student_code LIKE ? OR email LIKE ?
"""
params = (f"%{search_term}%", f"%{search_term}%")
rows = db.fetch_all(query, params)
```

The system includes automated security integration tests (`tests/test_security.py`) verifying that tautology payloads (`' OR '1'='1`), stacked injection attempts (`'; DROP TABLE students; --`), and union queries are rendered harmless as literal strings.

---

## 🚀 Quick Start Guide

### 1. Requirements
* Python 3.10+
* SQLite (built into Python, no external installation required)
* (Optional) MySQL Server 8.0+ and `pymysql` if running in MySQL mode.

### 2. Installation
Clone the repository and set up your virtual environment:

```bash
# Clone the repository
git clone <repository_url>
cd "Student RC Management"

# (Optional) Install enhanced terminal & MySQL dependencies
pip install -r requirements.txt
```

### 3. Run the Application

#### Option A: 🌐 Interactive Web Dashboard (Recommended)
Double-click `run_web.bat` or run:
```bash
python app.py
```
* Automatically opens in your browser at `http://127.0.0.1:5000`.
* Features real-time search, visual Chart.js graphs, interactive modals, printable transcripts, and 1-click CSV/JSON exports.

#### Option B: 💻 Interactive Terminal CLI
Double-click `run.bat` (and select Option 2) or run:
```bash
python main.py
```

#### Option C: 1-Click Interactive Launcher
Double-click `run.bat` in File Explorer to choose between Web Dashboard, CLI, or Automated Tests!

---

## 💻 CLI Menu Overview

```text
╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║            🎓  STUDENT RECORDS MANAGEMENT SYSTEM (SRMS)  🎓               ║
║                                                                           ║
║            Enterprise Edition • Python • SQL • SQLite • MySQL             ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝
  Active Engine: SQLITE | Status: .../data/student_records.db
---------------------------------------------------------------------------
  [1] 🎓  Student Management
  [2] 📚  Course Management
  [3] 📝  Grades & Enrollments
  [4] 📊  Reports & Analytics
  [5] ⚙️  Database & System Utilities
  [0] 🚪  Exit Application
---------------------------------------------------------------------------
```

### Academic Features Walkthrough:
* **Student Transcript**: View full student profile, course history, attempted vs. earned credit hours, and calculated cumulative GPA (4.0 scale).
* **Grade Recording**: Enter percentage scores (e.g. 94.5%) — the system automatically maps to letter grade (`A`) and grade point (`4.00`), updates status to `Completed`, and logs the timestamp.
* **Course Capacity Enforcement**: Enforces `max_capacity` on courses; rejects student enrollment if capacity is reached.
* **Honor Roll (Dean's List)**: Dynamically ranks top students meeting custom GPA thresholds (e.g. cumulative GPA $\ge 3.50$) and minimum credit hours.
* **Exporting**: One-click generation of `students_export.csv`, `grades_export.csv`, and `database_backup.json` inside the `exports/` folder.

---

## 🐬 MySQL Backend Setup

To switch to a MySQL backend:
1. Ensure MySQL is running and create the schema:
   ```bash
   mysql -u root -p < database/schema_mysql.sql
   ```
2. Configure environment variables (or update `config.py`):
   ```bash
   export SRMS_DB_ENGINE="mysql"
   export SRMS_MYSQL_HOST="localhost"
   export SRMS_MYSQL_PORT="3306"
   export SRMS_MYSQL_USER="root"
   export SRMS_MYSQL_PASSWORD="your_password"
   export SRMS_MYSQL_DB="student_records_db"
   ```
3. Run the application:
   ```bash
   python main.py --engine mysql
   ```

---

## 🧪 Running Automated Tests

Run the complete test suite (unit tests, CRUD integration, and SQL injection security):

```bash
python -m unittest discover tests -v
```

Test coverage includes:
* `test_validators.py`: Input format validation, age limits, date ordering, score-to-grade mappings.
* `test_crud.py`: Full CRUD for students, courses, enrollments, transcript GPA calculation, and cascade deletions.
* `test_security.py`: SQL injection attack simulations and parameterization verification.

---

## 📂 Project Directory Structure

```text
Student RC Management/
├── config.py                  # Global application & database settings
├── main.py                    # Application entry point & CLI parser
├── requirements.txt           # Python dependencies (pymysql, tabulate, etc.)
├── README.md                  # Comprehensive documentation
│
├── database/                  # Database management & schemas
│   ├── connection.py          # Unified DB connection & query executor
│   ├── schema_sqlite.sql      # 3NF SQLite schema DDL
│   ├── schema_mysql.sql       # 3NF MySQL schema DDL
│   └── seed_data.py           # Demonstration dataset generator
│
├── models/                    # Data models & entity definitions
│   ├── student.py             # Student domain model
│   ├── course.py              # Course domain model
│   └── enrollment.py          # Enrollment & Grade model
│
├── services/                  # Business logic & operations
│   ├── student_service.py     # Student CRUD & official transcripts
│   ├── course_service.py      # Course management & class rosters
│   ├── grade_service.py       # Enrollment, grading & GPA computations
│   └── report_service.py      # Analytics, Dean's list, CSV/JSON exports
│
├── utils/                     # Helper modules
│   ├── validators.py          # Strict data validation & sanitization
│   └── table_formatter.py     # Pure-Python formatted ASCII table renderer
│
├── cli/                       # Terminal user interface
│   ├── ui.py                  # ANSI styling, colors, prompts
│   └── menu_handler.py        # Menu navigation controllers
│
├── tests/                     # Automated test suites
│   ├── test_validators.py     # Unit tests for validation
│   ├── test_crud.py           # CRUD integration & GPA tests
│   └── test_security.py       # SQL injection defense tests
│
├── data/                      # Local storage directory (SQLite database)
└── exports/                   # Export directory (CSV & JSON backups)
```

---

## 📄 License
This project is open-source under the MIT License.
