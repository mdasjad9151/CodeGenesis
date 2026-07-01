from db.connection import Database
from core.logging import logger

DB_LIST = ['auth']

def start_database():
    databases =  DB_LIST
    for current_db_name in databases:
        try:
              Database.initialize(current_db_name)
              logger.info(f"Database '{current_db_name}' initialized successfully.")
        except Exception as e:
              logger.error(f"Error initializing database '{current_db_name}': {e}")