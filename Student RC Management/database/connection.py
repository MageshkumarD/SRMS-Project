"""
Unified Database Connection & Execution Manager.
Provides an enterprise-grade database interface supporting both SQLite and MySQL
with parameterized query normalization, automatic schema initialization,
and robust transaction handling to eliminate SQL injection vulnerabilities.
"""

import os
import sqlite3
import re
from typing import Any, Dict, List, Optional, Tuple, Union
from contextlib import contextmanager
from pathlib import Path

import config

# Try importing MySQL driver (PyMySQL)
try:
    import pymysql
    import pymysql.cursors
    PYMYSQL_AVAILABLE = True
except ImportError:
    PYMYSQL_AVAILABLE = False


class DatabaseManager:
    """Manages database connections, transactions, and unified query execution."""

    def __init__(self, engine: Optional[str] = None):
        self.engine = (engine or config.DB_ENGINE).lower()
        self._sqlite_path = config.SQLITE_DB_PATH
        self._mysql_config = config.MYSQL_CONFIG
        self._initialized = False

    def get_connection(self):
        """Creates and returns a raw connection for the configured engine."""
        if self.engine == "sqlite":
            Path(self._sqlite_path).parent.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(self._sqlite_path, timeout=10.0)
            conn.row_factory = sqlite3.Row
            # Ensure foreign key support is enabled
            conn.execute("PRAGMA foreign_keys = ON;")
            return conn
        elif self.engine == "mysql":
            if not PYMYSQL_AVAILABLE:
                raise RuntimeError(
                    "PyMySQL driver is not installed. Run 'pip install pymysql' to use MySQL backend."
                )
            conn = pymysql.connect(
                host=self._mysql_config["host"],
                port=self._mysql_config["port"],
                user=self._mysql_config["user"],
                password=self._mysql_config["password"],
                database=self._mysql_config["database"],
                charset=self._mysql_config["charset"],
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=False,
            )
            return conn
        else:
            raise ValueError(f"Unsupported database engine: '{self.engine}'. Use 'sqlite' or 'mysql'.")

    def _convert_query(self, query: str) -> str:
        """
        Normalizes parameterized queries.
        Standard queries in this application use '?' parameter placeholders.
        For MySQL, converts '?' to '%s'.
        """
        if self.engine == "mysql":
            # Replace '?' with '%s', avoiding quoted text
            return query.replace("?", "%s")
        return query

    @contextmanager
    def transaction(self):
        """Context manager for atomic database transactions with auto commit/rollback."""
        conn = self.get_connection()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def execute(self, query: str, params: Union[Tuple, List] = ()) -> int:
        """
        Executes an INSERT, UPDATE, or DELETE query with parameterized inputs.
        Returns the lastrowid or affected row count.
        """
        converted_query = self._convert_query(query)
        with self.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(converted_query, params)
            last_id = getattr(cursor, "lastrowid", None)
            row_count = getattr(cursor, "rowcount", 0)
            return last_id if (last_id and last_id > 0) else row_count

    def fetch_one(self, query: str, params: Union[Tuple, List] = ()) -> Optional[Dict[str, Any]]:
        """Executes a SELECT query and returns a single row as a dictionary."""
        converted_query = self._convert_query(query)
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(converted_query, params)
            row = cursor.fetchone()
            if row is None:
                return None
            return dict(row)
        finally:
            conn.close()

    def fetch_all(self, query: str, params: Union[Tuple, List] = ()) -> List[Dict[str, Any]]:
        """Executes a SELECT query and returns all matching rows as dictionaries."""
        converted_query = self._convert_query(query)
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(converted_query, params)
            rows = cursor.fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def initialize_schema(self, force: bool = False) -> None:
        """Runs the schema creation script to ensure all tables and indexes exist."""
        if self._initialized and not force:
            return

        schema_file = (
            Path(__file__).parent / "schema_sqlite.sql"
            if self.engine == "sqlite"
            else Path(__file__).parent / "schema_mysql.sql"
        )

        if not schema_file.exists():
            raise FileNotFoundError(f"Schema file not found: {schema_file}")

        with open(schema_file, "r", encoding="utf-8") as f:
            schema_sql = f.read()

        if self.engine == "sqlite":
            with self.transaction() as conn:
                conn.executescript(schema_sql)
        else:
            # MySQL multi-statement execution
            statements = [s.strip() for s in schema_sql.split(";") if s.strip()]
            with self.transaction() as conn:
                cursor = conn.cursor()
                for stmt in statements:
                    cursor.execute(stmt)

        self._initialized = True


# Global shared instance
db = DatabaseManager()
