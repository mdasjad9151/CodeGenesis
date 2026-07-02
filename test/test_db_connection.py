import pytest

from db.connection import Database
from core.logging import logger
from db.engine import start_database


def test_database_initialization():
    db_name = "auth"
    Database.initialize(db_name)

    engine = Database.get_engine()
    session = Database.get_session()

    assert engine is not None
    assert session is not None

    # Clean up
    Database.close()


def test_logging_initialization():
    assert logger is not None
    assert logger.handlers, "logger should have at least one handler after initialization"


def test_start_database_raises_on_initialization_error(monkeypatch):
    def fail_initialize(_db_name):
        raise RuntimeError("db unavailable")

    monkeypatch.setattr(Database, "initialize", fail_initialize)

    with pytest.raises(RuntimeError, match="db unavailable"):
        start_database("auth")


if __name__ == "__main__":
    test_database_initialization()
    test_logging_initialization()
    print("Database initialization test passed.")