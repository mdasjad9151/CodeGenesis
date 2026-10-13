import json

from db.connection import Database
from sqlalchemy import text


class ProblemRepository:
    def __init__(self):
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
                    constraints,
                    examples,
                    sample_testcases,
                    topics,
                    hints,
                    starter_code
                FROM {self.problem_table}
                WHERE problem_id = :problem_id
            """
            result = self.db.execute(text(query), {"problem_id": problem_id})
            return result.mappings().first()
        finally:
            self.db.close()

    def get_testcases(self, problem_id: int):
        try:
            query = f"""
                SELECT problem_id, sample_testcases, hidden_testcases
                FROM {self.problem_table}
                WHERE problem_id = :problem_id
            """
            result = self.db.execute(text(query), {"problem_id": problem_id})
            return result.mappings().first()
        finally:
            self.db.close()

    @staticmethod
    def _to_params(problem: dict) -> dict:
        return {
            "title": problem["title"],
            "difficulty": problem["difficulty"],
            "statement": problem["description"],
            "input_format": problem.get("input_format"),
            "output_format": problem.get("output_format"),
            "constraints": json.dumps(problem.get("constraints", [])),
            "examples": json.dumps(problem.get("examples", [])),
            "sample_testcases": json.dumps(problem.get("sample_testcases", [])),
            "hidden_testcases": json.dumps(problem["hidden_testcases"]),
            "topics": problem.get("topics", []),
            "hints": json.dumps(problem.get("hints", [])),
            "starter_code": json.dumps(problem.get("starter_code", {})),
        }

    def create_problem(self, problem: dict, created_by: str | None) -> int:
        try:
            query = f"""
                INSERT INTO {self.problem_table} (
                    title, difficulty, statement, input_format, output_format,
                    constraints, examples, sample_testcases, hidden_testcases,
                    topics, hints, starter_code, created_by
                ) VALUES (
                    :title, :difficulty, :statement, :input_format, :output_format,
                    CAST(:constraints AS JSONB), CAST(:examples AS JSONB),
                    CAST(:sample_testcases AS JSONB), CAST(:hidden_testcases AS JSONB),
                    :topics, CAST(:hints AS JSONB), CAST(:starter_code AS JSONB), :created_by
                )
                RETURNING problem_id
            """
            params = self._to_params(problem) | {"created_by": created_by}
            problem_id = self.db.execute(text(query), params).scalar_one()
            self.db.commit()
            return problem_id
        except Exception as e:
            self.db.rollback()
            raise e
        finally:
            self.db.close()

    def update_problem(self, problem_id: int, problem: dict) -> bool:
        try:
            query = f"""
                UPDATE {self.problem_table} SET
                    title = :title,
                    difficulty = :difficulty,
                    statement = :statement,
                    input_format = :input_format,
                    output_format = :output_format,
                    constraints = CAST(:constraints AS JSONB),
                    examples = CAST(:examples AS JSONB),
                    sample_testcases = CAST(:sample_testcases AS JSONB),
                    hidden_testcases = CAST(:hidden_testcases AS JSONB),
                    topics = :topics,
                    hints = CAST(:hints AS JSONB),
                    starter_code = CAST(:starter_code AS JSONB),
                    updated_at = CURRENT_TIMESTAMP
                WHERE problem_id = :problem_id
            """
            params = self._to_params(problem) | {"problem_id": problem_id}
            result = self.db.execute(text(query), params)
            self.db.commit()
            return result.rowcount == 1
        except Exception as e:
            self.db.rollback()
            raise e
        finally:
            self.db.close()

    def delete_problem(self, problem_id: int) -> bool:
        try:
            query = f"DELETE FROM {self.problem_table} WHERE problem_id = :problem_id"
            result = self.db.execute(text(query), {"problem_id": problem_id})
            self.db.commit()
            return result.rowcount == 1
        except Exception as e:
            self.db.rollback()
            raise e
        finally:
            self.db.close()

    def find_problem_ids(self, topic: str, difficulty: str, limit: int) -> list[int]:
        """Random existing problems with this topic tag and difficulty (for instant contests)."""
        try:
            query = f"""
                SELECT problem_id
                FROM {self.problem_table}
                WHERE :topic = ANY(topics) AND difficulty = :difficulty
                ORDER BY random()
                LIMIT :limit
            """
            result = self.db.execute(text(query), {"topic": topic, "difficulty": difficulty, "limit": limit})
            return [row[0] for row in result]
        finally:
            self.db.close()
