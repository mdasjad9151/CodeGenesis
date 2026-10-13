from db.connection import Database
from sqlalchemy import text


class DailyRepository:
    def __init__(self):
        self.db = Database.get_session()
        self.table_name = "daily_problems"

    def get_daily(self, challenge_date):
        try:
            query = f"""
                SELECT d.challenge_date, d.difficulty, d.topic, d.problem_id, p.title
                FROM {self.table_name} d
                JOIN problems p ON p.problem_id = d.problem_id
                WHERE d.challenge_date = :challenge_date
                ORDER BY CASE d.difficulty WHEN 'easy' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END
            """
            result = self.db.execute(text(query), {"challenge_date": challenge_date})
            return result.mappings().all()
        finally:
            self.db.close()

    def set_daily(self, challenge_date, difficulty: str, problem_id: int, topic: str | None):
        try:
            query = f"""
                INSERT INTO {self.table_name} (challenge_date, difficulty, problem_id, topic)
                VALUES (:challenge_date, :difficulty, :problem_id, :topic)
                ON CONFLICT (challenge_date, difficulty)
                DO UPDATE SET problem_id = EXCLUDED.problem_id, topic = EXCLUDED.topic
            """
            params = {"challenge_date": challenge_date, "difficulty": difficulty, "problem_id": problem_id, "topic": topic}
            self.db.execute(text(query), params)
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise e
        finally:
            self.db.close()
