from db.connection import Database
from sqlalchemy import text


class ProblemRepository:
    def __init__(self):
        Database.initialize("auth")
        self.db = Database.get_session()
        self.problem_table = "problems"

    def get_problem_count(self) -> int:
        try:
            query = f"SELECT COUNT(*) FROM {self.problem_table}"
            result = self.db.execute(text(query)).scalar()
            return result or 0
        finally:
            self.db.close()

    def get_problem_list(self, limit: int, offset: int):
        try:
            query = f"""
                SELECT problem_id, title, difficulty
                FROM {self.problem_table}
                ORDER BY created_at DESC, problem_id DESC
                LIMIT :limit OFFSET :offset
            """
            result = self.db.execute(text(query), {"limit": limit, "offset": offset})
            return result.mappings().all()
        finally:
            self.db.close()

    def get_problem_by_id(self, problem_id: int):
        try:
            query = f"""
                SELECT
                    problem_id,
                    title,
                    difficulty,
                    statement,
                    input_format,
                    output_format,
                    examples,
                    sample_testcases,
                    topics,
                    starter_code
                FROM {self.problem_table}
                WHERE problem_id = :problem_id
            """
            result = self.db.execute(text(query), {"problem_id": problem_id})
            return result.mappings().first()
        finally:
            self.db.close()
