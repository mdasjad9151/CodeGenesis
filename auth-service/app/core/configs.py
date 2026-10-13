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

    def jwt_config(self):
        return {
            "secret_key": os.getenv('JWT_SECRET_KEY'),
            'algorithm': os.getenv('JWT_ALGORITHM'),
            "access_token_expire_minutes": int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "15")),
            "refresh_token_expire_days": int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7")),
        }
