from dotenv import load_dotenv
import os
load_dotenv()
class ConfigLoader:
    def __init__(self, config_path: str =None):
        self.config_path = config_path
    def get_db_config(self):
        return {
            'postgre_uri': os.getenv('POSTGRESQL_URI'),
        }
