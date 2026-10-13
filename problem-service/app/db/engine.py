from pathlib import Path

from db.connection import Database
from core.logging import logger

DB_NAME = "problems"
# problem-service/problem.sql (two levels above app/db/)
SCHEMA_FILE = Path(__file__).resolve().parents[2] / "problem.sql"


def start_database():
    """Connect to the problems database and apply problem.sql. Fails fast if Postgres is unreachable."""
    Database.initialize(DB_NAME)
    with Database.get_engine().begin() as conn:
        conn.exec_driver_sql(SCHEMA_FILE.read_text())
    logger.info(f"Database '{DB_NAME}' initialized and schema applied.")
