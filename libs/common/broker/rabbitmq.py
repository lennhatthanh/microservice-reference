import json
import logging
import time
from collections.abc import Callable

import pika

logger = logging.getLogger(__name__)


class RabbitMQClient:
    """Small RabbitMQ adapter used by services.

    This keeps broker details out of application services. Application code
    should publish integration events, not talk to pika directly.
    """

    def __init__(self, url: str, exchange: str = "ecommerce.events") -> None:
        self.url = url
        self.exchange = exchange

    def publish(self, routing_key: str, payload: dict) -> None:
        connection = pika.BlockingConnection(pika.URLParameters(self.url))
        try:
            channel = connection.channel()
            channel.exchange_declare(
                exchange=self.exchange,
                exchange_type="topic",
                durable=True,
            )
            channel.basic_publish(
                exchange=self.exchange,
                routing_key=routing_key,
                body=json.dumps(payload, default=str).encode(),
                properties=pika.BasicProperties(
                    content_type="application/json",
                    delivery_mode=2,
                ),
            )
        finally:
            connection.close()

    def consume(
        self,
        queue: str,
        bindings: list[str],
        handler: Callable[[dict], None],
        max_retries: int = 3,
    ) -> None:
        while True:
            try:
                connection = pika.BlockingConnection(pika.URLParameters(self.url))
                channel = connection.channel()
                channel.exchange_declare(
                    exchange=self.exchange,
                    exchange_type="topic",
                    durable=True,
                )
                channel.queue_declare(queue=queue, durable=True)
                dlq = f"{queue}.dlq"
                channel.queue_declare(queue=dlq, durable=True)
                for binding in bindings:
                    channel.queue_bind(exchange=self.exchange, queue=queue, routing_key=binding)

                def callback(ch, method, properties, body):
                    try:
                        handler(json.loads(body.decode()))
                        ch.basic_ack(delivery_tag=method.delivery_tag)
                    except Exception:
                        logger.exception("RabbitMQ consumer failed for queue=%s", queue)
                        headers = dict(properties.headers or {})
                        retry_count = int(headers.get("x-retry-count", 0))
                        ch.basic_ack(delivery_tag=method.delivery_tag)
                        if retry_count >= max_retries:
                            channel.basic_publish(
                                exchange="",
                                routing_key=dlq,
                                body=body,
                                properties=pika.BasicProperties(
                                    content_type="application/json",
                                    delivery_mode=2,
                                    headers=headers,
                                ),
                            )
                            return
                        headers["x-retry-count"] = retry_count + 1
                        channel.basic_publish(
                            exchange="",
                            routing_key=queue,
                            body=body,
                            properties=pika.BasicProperties(
                                content_type="application/json",
                                delivery_mode=2,
                                headers=headers,
                            ),
                        )

                channel.basic_qos(prefetch_count=1)
                channel.basic_consume(queue=queue, on_message_callback=callback)
                channel.start_consuming()
            except Exception:
                logger.exception("RabbitMQ consumer reconnecting for queue=%s", queue)
                time.sleep(3)
