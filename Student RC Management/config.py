"""
Configuration Management for Student Records Management System.
Supports seamless switching between SQLite and MySQL backends,
configurable via environment variables or direct settings.
"""

import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
EXPORTS_DIR = BASE_DIR / "exports"
DATA_DIR.mkdir(parents=True, exist_ok=True)
EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

# Database Backend Configuration: 'sqlite' or 'mysql'
DB_ENGINE = os.getenv("SRMS_DB_ENGINE", "sqlite").lower()

# SQLite Specific Settings
SQLITE_DB_PATH = os.getenv("SRMS_SQLITE_PATH", str(DATA_DIR / "student_records.db"))

# MySQL Specific Settings
MYSQL_CONFIG = {
    "host": os.getenv("SRMS_MYSQL_HOST", "localhost"),
    "port": int(os.getenv("SRMS_MYSQL_PORT", 3306)),
    "user": os.getenv("SRMS_MYSQL_USER", "root"),
    "password": os.getenv("SRMS_MYSQL_PASSWORD", ""),
    "database": os.getenv("SRMS_MYSQL_DB", "student_records_db"),
    "charset": "utf8mb4",
    "autocommit": False,
}

# Grading Scale Standard (4.0 GPA scale)
GRADE_SCALE = {
    "A+": {"min_score": 97.0, "points": 4.0},
    "A":  {"min_score": 93.0, "points": 4.0},
    "A-": {"min_score": 90.0, "points": 3.7},
    "B+": {"min_score": 87.0, "points": 3.3},
    "B":  {"min_score": 83.0, "points": 3.0},
    "B-": {"min_score": 80.0, "points": 2.7},
    "C+": {"min_score": 77.0, "points": 2.3},
    "C":  {"min_score": 73.0, "points": 2.0},
    "C-": {"min_score": 70.0, "points": 1.7},
    "D":  {"min_score": 60.0, "points": 1.0},
    "F":  {"min_score": 0.0,  "points": 0.0},
}

# System Display Settings
PAGE_SIZE = 10
APP_NAME = "Student Records Management System"
APP_VERSION = "2.0.0"
