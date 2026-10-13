from db.connection import Database
from sqlalchemy import text


class ContestRepository:
    def __init__(self):
        self.db = Database.get_session()
        self.table_name = "contests"

    def create_contest(self, title: str, topic: str, difficulty: str, created_by: str, problem_ids: list[int]) -> str:
        try:
            query = f"""
                INSERT INTO {self.table_name} (title, topic, difficulty, created_by)
                VALUES (:title, :topic, :difficulty, :created_by)
                RETURNING contest_id
            """
            params = {"title": title, "topic": topic, "difficulty": difficulty, "created_by": created_by}
            contest_id = self.db.execute(text(query), params).scalar_one()
            link_query = """
                INSERT INTO contest_problems (contest_id, problem_id, position)
                VALUES (:contest_id, :problem_id, :position)
            """
            self.db.execute(text(link_query), [
                {"contest_id": contest_id, "problem_id": problem_id, "position": position}
                for position, problem_id in enumerate(problem_ids, start=1)
            ])
            self.db.commit()
            return str(contest_id)
        except Exception as e:
            self.db.rollback()
            raise e
        finally:
            self.db.close()

    def get_contest(self, contest_id: str):
        try:
            query = f"""
                SELECT contest_id, title, topic, difficulty, created_by, created_at
                FROM {self.table_name}
                WHERE contest_id = :contest_id
            """
            return self.db.execute(text(query), {"contest_id": contest_id}).mappings().first()
        finally:
            self.db.close()

    def get_contest_problems(self, contest_id: str):
        try:
            query = """
                SELECT cp.position, p.problem_id, p.title, p.difficulty
                FROM contest_problems cp
                JOIN problems p ON p.problem_id = cp.problem_id
                WHERE cp.contest_id = :contest_id
                ORDER BY cp.position
            """
            return self.db.execute(text(query), {"contest_id": contest_id}).mappings().all()
        finally:
            self.db.close()

    def is_problem_in_contest(self, contest_id: str, problem_id: int) -> bool:
        try:
            query = "SELECT 1 FROM contest_problems WHERE contest_id = :contest_id AND problem_id = :problem_id"
            return self.db.execute(text(query), {"contest_id": contest_id, "problem_id": problem_id}).first() is not None
        finally:
            self.db.close()

    def get_scores(self, contest_id: str, limit: int = 20):
        """Score = number of distinct contest problems the user got Accepted (inside this contest)."""
        try:
            query = """
                SELECT user_id,
                       COUNT(DISTINCT problem_id) AS solved,
                       MAX(updated_at) AS last_accepted_at
                FROM submissions
                WHERE contest_id = :contest_id AND verdict = 'Accepted'
                GROUP BY user_id
                ORDER BY solved DESC, last_accepted_at ASC
                LIMIT :limit
            """
            return self.db.execute(text(query), {"contest_id": contest_id, "limit": limit}).mappings().all()
        finally:
            self.db.close()

    def get_user_solved(self, contest_id: str, user_id: str) -> set[int]:
        try:
            query = """
                SELECT DISTINCT problem_id FROM submissions
                WHERE contest_id = :contest_id AND user_id = :user_id AND verdict = 'Accepted'
            """
            return {row[0] for row in self.db.execute(text(query), {"contest_id": contest_id, "user_id": user_id})}
        finally:
            self.db.close()
