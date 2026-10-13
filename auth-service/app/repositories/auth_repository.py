from db.connection import Database
from sqlalchemy import text
from datetime import datetime, timedelta, timezone


class AuthRepository:
    def __init__(self):
        self.db = Database.get_session()
        self.table_name = "users"

    def user_exists(self, email: str) -> bool:
        try:
            query = f"SELECT COUNT(*) FROM {self.table_name} WHERE email = :email"
            result = self.db.execute(text(query), {"email": email}).scalar()
            return result > 0
        finally:
            self.db.close()


    def create_user(self, email: str, password: str, otp: str) -> str:
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)
        try:
            query = f"INSERT INTO {self.table_name} (email, hashed_password) VALUES (:email, :hashed_password) RETURNING id"
            result = self.db.execute(text(query), {"email": email, "hashed_password": password})
            user_id = result.scalar_one()
            otp_query = f"INSERT INTO auth_otps (user_id, otp_code, expires_at) VALUES (:user_id, :otp_code, :expires_at)"
            self.db.execute(text(otp_query), {"user_id": user_id, "otp_code": otp, "expires_at": expires_at})
            self.db.commit()
            return str(user_id)
        except Exception as e:
            self.db.rollback()
            raise e
        finally:
            self.db.close()

    def get_user_by_email(self, email: str):
        try:
            query = f"""
                SELECT id, email, is_verified
                FROM {self.table_name}
                WHERE email = :email
            """
            result = self.db.execute(text(query), {"email": email})
            return result.mappings().first()
        finally:
            self.db.close()

    def get_login_user_by_email(self, email: str):
        try:
            query = f"""
                SELECT id, email, hashed_password, role, is_verified, is_active
                FROM {self.table_name}
                WHERE email = :email
            """
            result = self.db.execute(text(query), {"email": email})
            return result.mappings().first()
        finally:
            self.db.close()

    def get_user_by_id(self, user_id: str):
        try:
            query = f"""
                SELECT id, email, role, is_verified, is_active
                FROM {self.table_name}
                WHERE id = :user_id
            """
            result = self.db.execute(text(query), {"user_id": user_id})
            return result.mappings().first()
        finally:
            self.db.close()

    def get_active_registration_otp(self, user_id: str):
        try:
            query = """
                SELECT id, otp_code, expires_at, is_used
                FROM auth_otps
                WHERE user_id = :user_id
                  AND purpose = 'registration'
                  AND is_used = FALSE
                ORDER BY created_at DESC
                LIMIT 1
            """
            result = self.db.execute(text(query), {"user_id": user_id})
            return result.mappings().first()
        finally:
            self.db.close()

    def mark_user_as_verified(self, user_id: str, otp_id: str):
        try:
            user_query = f"""
                UPDATE {self.table_name}
                SET is_verified = TRUE, updated_at = CURRENT_TIMESTAMP
                WHERE id = :user_id
            """
            otp_query = """
                DELETE FROM auth_otps
                WHERE id = :otp_id
            """
            self.db.execute(text(user_query), {"user_id": user_id})
            self.db.execute(text(otp_query), {"otp_id": otp_id})
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise e
        finally:
            self.db.close()

    def get_refresh_token(self, jti: str):
        try:
            query = """
                SELECT user_id, jti, expires_at, revoked_at
                FROM auth_refresh_tokens
                WHERE jti = :jti
            """
            result = self.db.execute(text(query), {"jti": jti})
            return result.mappings().first()
        finally:
            self.db.close()

    def save_refresh_token(self, user_id: str, jti: str, expires_at: datetime, replaces_jti: str | None = None):
        """Store a new refresh token jti. If replaces_jti is given, revoke that one in the same transaction."""
        try:
            if replaces_jti:
                revoke_query = """
                    UPDATE auth_refresh_tokens
                    SET revoked_at = CURRENT_TIMESTAMP, replaced_by_jti = :new_jti
                    WHERE jti = :old_jti AND revoked_at IS NULL
                """
                result = self.db.execute(text(revoke_query), {"new_jti": jti, "old_jti": replaces_jti})
                if result.rowcount != 1:
                    # Someone else already rotated this token
                    self.db.rollback()
                    return False

            insert_query = """
                INSERT INTO auth_refresh_tokens (user_id, jti, expires_at)
                VALUES (:user_id, :jti, :expires_at)
            """
            self.db.execute(text(insert_query), {"user_id": user_id, "jti": jti, "expires_at": expires_at})
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            raise e
        finally:
            self.db.close()
