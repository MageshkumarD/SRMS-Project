"""
Student Records Management System (SRMS)
Main Application Entry Point.
"""

import argparse
import sys
import config
from database.connection import db, DatabaseManager
from database.seed_data import seed_database
from cli.menu_handler import MenuHandler


def parse_args():
    parser = argparse.ArgumentParser(
        description="Student Records Management System (Python, SQL, SQLite, MySQL)"
    )
    parser.add_argument(
        "--web",
        action="store_true",
        help="Launch modern interactive browser web dashboard (http://127.0.0.1:5000)",
    )
    parser.add_argument(
        "--engine",
        choices=["sqlite", "mysql"],
        default=config.DB_ENGINE,
        help="Specify database engine backend (default: sqlite)",
    )
    parser.add_argument(
        "--seed",
        action="store_true",
        help="Seed the database with sample departments, students, courses, and grades",
    )
    parser.add_argument(
        "--reset-db",
        action="store_true",
        help="Wipe and recreate database schema before starting",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    config.DB_ENGINE = args.engine

    # Initialize manager
    db_mgr = DatabaseManager(engine=args.engine)

    try:
        db_mgr.initialize_schema(force=args.reset_db)
    except Exception as e:
        print(f"Error initializing database engine '{args.engine}': {e}")
        sys.exit(1)

    if args.seed:
        print("Seeding sample academic records...")
        seed_database(db_mgr, reset=args.reset_db)
        print("Seeding complete.")

    if args.web:
        from app import run_web
        run_web()
        return

    # Launch CLI
    app = MenuHandler(db_manager=db_mgr)
    try:
        app.start()
    except KeyboardInterrupt:
        print("\n\nOperation interrupted by user. Exiting...")
        sys.exit(0)


if __name__ == "__main__":
    main()
