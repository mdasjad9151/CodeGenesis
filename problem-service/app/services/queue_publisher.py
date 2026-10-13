import json

import pika

from core.configs import ConfigLoader

config = ConfigLoader()


def publish_submission(message: dict) -> None:
    """Publish one message to the durable `submissions` queue.

    A short-lived connection per publish keeps this simple and thread-safe
    (submissions are not frequent enough for this to matter).
    """
    rabbit = config.rabbitmq_config()
    connection = pika.BlockingConnection(pika.URLParameters(rabbit["url"]))
    try:
        channel = connection.channel()
        channel.queue_declare(queue=rabbit["submission_queue"], durable=True)
        channel.basic_publish(
            exchange="",
            routing_key=rabbit["submission_queue"],
            body=json.dumps(message),
            properties=pika.BasicProperties(
                content_type="application/json",
                delivery_mode=pika.DeliveryMode.Persistent,
            ),
        )
    finally:
        connection.close()
