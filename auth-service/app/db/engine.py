from pathlib import Path

from db.connection import Database
from core.logging import logger

DB_NAME = "auth"
# auth-service/db.sql (two levels above app/db/)
SCHEMA_FILE = Path(__file__).resolve().parents[2] / "db.sql"


def start_database():
    """Connect to the auth database and apply db.sql. Fails fast if Postgres is unreachable."""
    Database.initialize(DB_NAME)
    with Database.get_engine().begin() as conn:
        conn.exec_driver_sql(SCHEMA_FILE.read_text())
    logger.info(f"Database '{DB_NAME}' initialized and schema applied.")
