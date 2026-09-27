"""SQLite connection and initialization helpers for PakYield Lab."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from pakyield.config import DATABASE_PATH, SQL_DIR

DEFAULT_SCHEMA_PATH = SQL_DIR / "001_schema.sql"


def get_connection(
    database_path: Path = DATABASE_PATH,
) -> sqlite3.Connection:
    """Create a configured SQLite connection.

    Foreign-key enforcement is enabled for every connection because SQLite
    requires this setting on a per-connection basis.
    """

    database_path.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row

    connection.execute("PRAGMA foreign_keys = ON;")

    return connection


def initialize_database(
    database_path: Path = DATABASE_PATH,
    schema_path: Path = DEFAULT_SCHEMA_PATH,
) -> None:
    """Create the PakYield SQLite schema if it does not already exist."""

    if not schema_path.is_file():
        raise FileNotFoundError(f"Schema file does not exist: {schema_path}")

    schema_sql = schema_path.read_text(encoding="utf-8")

    connection = get_connection(database_path)

    try:
        connection.executescript(schema_sql)
        connection.commit()
    finally:
        connection.close()
