"""Initialize the local PakYield SQLite research database."""

from pakyield.config import DATABASE_PATH
from pakyield.database.connection import initialize_database


def main() -> None:
    """Initialize the PakYield database and report its location."""

    initialize_database()

    print("PakYield database initialization: PASS")
    print(f"Database: {DATABASE_PATH}")


if __name__ == "__main__":
    main()
