from sqlalchemy import create_engine,text
from sqlalchemy.orm import sessionmaker
from core.configs import ConfigLoader

class Database:
    _engine = None
    _SessionLocal = None
    postgre_uri = ConfigLoader().get_db_config()['postgre_uri']
    @classmethod
    def initialize(cls, database_name: str):
        if cls._engine is not None:
            return

        database_url = f"{cls.postgre_uri}{database_name}"
        cls._engine = create_engine(
            database_url,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
            echo=False,
        )
        with cls._engine.connect() as conn:
            conn.execute(text("SELECT 1"))

        cls._SessionLocal = sessionmaker(
            bind=cls._engine,
            autoflush=False,
            autocommit=False,
        )

    @classmethod
    def get_session(cls):
        if cls._SessionLocal is None:
            raise RuntimeError("Database not initialized.")
        return cls._SessionLocal()

    @classmethod
    def dispose(cls):
        if cls._engine:
            cls._engine.dispose()