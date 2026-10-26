"""RabbitMQ consumer for the `submissions` queue, run in a background thread inside ai-service.

Flow per message: mark running -> fetch test cases -> grade with Judge0 -> PUT result to problem-service.
Results go back over HTTP (not a `results` queue) so problem-service doesn't need its own consumer thread.
"""
import json
import threading
import time

import pika

from core.configs import ConfigLoader
from core.logging import logger
from services.judge0_client import Judge0Client
from services.judge_service import grade
from services.problem_client import ProblemClient

config = ConfigLoader()


def process_message(body: bytes, judge: Judge0Client, problems: ProblemClient) -> None:
    message = json.loads(body)
    submission_id = message["submission_id"]
    logger.info(f"Judging submission {submission_id} ({message['language']}, problem {message['problem_id']})")

    try:
        problems.save_result(submission_id, {"status": "running"})
        testcases = problems.get_testcases(message["problem_id"])
        result = grade(judge, message["source_code"], message["language"], testcases)
    except Exception as e:
        logger.error(f"Judging submission {submission_id} failed: {e}")
        result = {"status": "failed", "verdict": "Internal Error", "error_output": "Judge unavailable, please resubmit"}

    problems.save_result(submission_id, result)
    logger.info(f"Submission {submission_id}: {result['verdict']} ({result.get('passed_count')}/{result.get('total_count')})")


class SubmissionConsumer:
    def __init__(self):
        self.connected = False
        self.thread = threading.Thread(target=self._run_forever, name="submission-consumer", daemon=True)

    def start(self) -> None:
        self.thread.start()

    def is_alive(self) -> bool:
        return self.thread.is_alive() and self.connected

    def _on_message(self, channel, method, properties, body) -> None:
        try:
            process_message(body, self.judge, self.problems)
        except Exception as e:
            # Bad JSON, or problem-service unreachable when saving the result. Don't requeue forever.
            logger.error(f"Dropping submission message: {e}")
        channel.basic_ack(delivery_tag=method.delivery_tag)

    def _run_forever(self) -> None:
        rabbit = config.rabbitmq_config()
        self.judge = Judge0Client()
        self.problems = ProblemClient()

        while True:
            try:
                params = pika.URLParameters(rabbit["url"])
                params.heartbeat = 600  # judging one submission can take a while
                connection = pika.BlockingConnection(params)
                channel = connection.channel()
                channel.queue_declare(queue=rabbit["submission_queue"], durable=True)
                channel.basic_qos(prefetch_count=1)  # one submission at a time
                channel.basic_consume(queue=rabbit["submission_queue"], on_message_callback=self._on_message)
                self.connected = True
                logger.info(f"Consuming from queue '{rabbit['submission_queue']}'")
                channel.start_consuming()
            except Exception as e:
                self.connected = False
                logger.error(f"RabbitMQ consumer error: {e}. Reconnecting in 5s")
                time.sleep(5)
