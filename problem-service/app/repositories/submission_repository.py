from db.connection import Database
from sqlalchemy import text


class SubmissionRepository:
    def __init__(self):
        self.db = Database.get_session()
        self.table_name = "submissions"

    def create_submission(self, user_id: str, problem_id: int, language: str, source_code: str,
                          contest_id: str | None = None) -> str:
        try:
            query = f"""
                INSERT INTO {self.table_name} (user_id, problem_id, contest_id, language, source_code)
                VALUES (:user_id, :problem_id, :contest_id, :language, :source_code)
                RETURNING submission_id
            """
            params = {"user_id": user_id, "problem_id": problem_id, "contest_id": contest_id,
                      "language": language, "source_code": source_code}
            submission_id = self.db.execute(text(query), params).scalar_one()
            self.db.commit()
            return str(submission_id)
        except Exception as e:
            self.db.rollback()
            raise e
        finally:
            self.db.close()

    def get_submission(self, submission_id: str):
        try:
            query = f"""
                SELECT submission_id, user_id, problem_id, contest_id, language, status, verdict,
                       passed_count, total_count, runtime_ms, memory_kb, error_output, created_at
                FROM {self.table_name}
                WHERE submission_id = :submission_id
            """
            result = self.db.execute(text(query), {"submission_id": submission_id})
            return result.mappings().first()
        finally:
            self.db.close()

    def update_result(self, submission_id: str, result: dict) -> bool:
        try:
            query = f"""
                UPDATE {self.table_name} SET
                    status = :status,
                    verdict = :verdict,
                    passed_count = :passed_count,
                    total_count = :total_count,
                    runtime_ms = :runtime_ms,
                    memory_kb = :memory_kb,
                    error_output = :error_output,
                    updated_at = CURRENT_TIMESTAMP
                WHERE submission_id = :submission_id
            """
            updated = self.db.execute(text(query), result | {"submission_id": submission_id})
            self.db.commit()
            return updated.rowcount == 1
        except Exception as e:
            self.db.rollback()
            raise e
        finally:
            self.db.close()
