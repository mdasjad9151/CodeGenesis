from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

load_dotenv()

POSTGRESQL_URI = os.getenv("POSTGRESQL_URI")


class Database:

    _engine = None
    _SessionLocal = None

    @classmethod
    def initialize(cls, db_name: str):

        if cls._engine is None:

            DATABASE_URL = f"{POSTGRESQL_URI}/{db_name}"

            cls._engine = create_engine(
                DATABASE_URL,
                pool_pre_ping=True,
                pool_size=10,
                max_overflow=20,
                echo=False,
            )

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