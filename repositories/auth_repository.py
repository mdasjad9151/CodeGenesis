from db.connection import Database
from sqlalchemy import text
from datetime import datetime, timedelta

class AuthRepository:
    def __init__(self):
        Database.initialize("auth")
        self.db = Database.get_session()
        self.table_name = "users"

    def user_exists(self, email: str) -> bool:
        query = f"SELECT COUNT(*) FROM {self.table_name} WHERE email = :email"
        result = self.db.execute(text(query), {"email": email}).scalar()
        return result > 0


    def create_user(self, email: str, password: str, otp: str) -> str:

        expires_at = datetime.utcnow() + timedelta(minutes=5)
        try:
            query = f"INSERT INTO {self.table_name} (email, hashed_password) VALUES (:email, :hashed_password) RETURNING id"
            result =self.db.execute(text(query), { "email": email, "hashed_password": password})
            user_id = result.scalar_one()
            otp_query = f"INSERT INTO auth_otps (user_id, otp_code, expires_at) VALUES (:user_id, :otp_code, :expires_at)"
            self.db.execute(text(otp_query), {"user_id": user_id, "otp_code": otp, "expires_at": expires_at})
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise e
        finally:
            self.db.close()