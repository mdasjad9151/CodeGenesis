from sqlalchemy import create_engine,text
from sqlalchemy.orm import sessionmaker
from core.configs import ConfigLoader

class Database:

    _engine = None
    _SessionLocal = None
    postger_uri =  ConfigLoader().get_db_config()['postgre_uri']

    @classmethod
    def initialize(cls, db_name: str):

        if cls._engine is None:
            DATABASE_URL = f"{cls.postger_uri}{db_name}"
            cls._engine = create_engine(
                DATABASE_URL,
                pool_pre_ping=True,
                pool_size=10,
                max_overflow=20,
                echo=False,
            )
            # Force connection
            with cls._engine.connect() as conn:
                conn.execute(text("SELECT 1"))

            cls._SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=cls._engine,
            )

    @classmethod
    def get_engine(cls):
        return cls._engine

    @classmethod
    def get_session(cls):
        return cls._SessionLocal()

    @classmethod
    def close(cls):
        if cls._engine:
            cls._engine.dispose()