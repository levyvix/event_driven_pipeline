"""Message consumer for weather data."""

import json

import pika
from pika.adapters.blocking_connection import BlockingChannel
import requests
from loguru import logger

from .config import settings


class MessageConsumer:
    """
    RabbitMQ message consumer that processes weather data.

    Receives messages from a RabbitMQ queue, parses JSON weather data,
    and forwards it to the internal weather API. Uses manual acknowledgment
    for reliability with retry logic for transient failures.
    """

    def __init__(self) -> None:
        """Initialize RabbitMQ connection and channel."""
        logger.info("Connecting to RabbitMQ")
        self.connection: pika.BlockingConnection = pika.BlockingConnection(
            pika.ConnectionParameters(host=settings.RABBIT_HOST)
        )
        self.channel: BlockingChannel = self.connection.channel()
        self.channel.queue_declare(queue=settings.QUEUE_NAME)
        logger.success("Connected to RabbitMQ")

    def callback(
        self,
        channel: BlockingChannel,
        method,
        properties,
        body: bytes,
    ) -> None:
        """
        Process a message from the RabbitMQ queue.

        Attempts to parse message JSON and post it to the internal API.
        On success, acknowledges the message. On JSON decode errors,
        rejects without requeue (discards malformed messages).
        On network errors, rejects with requeue for retry.

        Args:
            channel: RabbitMQ channel
            method: AMQP method frame
            properties: AMQP message properties
            body: Raw message body bytes
        """
        try:
            logger.info("Received message from RabbitMQ")
            logger.debug(f"Message body: {body}")

            # Parse the message
            message_data: dict = json.loads(body)

            # Send to internal API
            logger.info(f"Sending data to API: {settings.API_URL}")
            response: requests.Response = requests.post(
                settings.API_URL,
                json=message_data,
                headers={"Content-Type": "application/json"},
                timeout=10,
            )
            response.raise_for_status()

            logger.success(
                f"Data successfully sent to API. Status: {response.status_code}"
            )

            # Acknowledge the message
            if channel.is_open:
                channel.basic_ack(delivery_tag=method.delivery_tag)
                logger.info("Message acknowledged")

        except json.JSONDecodeError as decode_error:
            logger.error(f"Failed to decode message JSON: {decode_error}")
            # Reject and don't requeue malformed messages
            channel.basic_nack(
                delivery_tag=method.delivery_tag, requeue=False
            ) if channel.is_open else None

        except requests.exceptions.RequestException as request_error:
            logger.error(f"Failed to send data to API: {request_error}")
            # Reject and requeue for retry
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

        except Exception as unexpected_error:
            logger.error(f"Unexpected error processing message: {unexpected_error}")
            # Reject and requeue for retry
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    def start_consuming(self) -> None:
        """
        Start consuming messages from the configured queue.

        Processes one message at a time (prefetch_count=1) with manual
        acknowledgment for reliability. Handles graceful shutdown on
        KeyboardInterrupt.
        """
        logger.info(f"Starting to consume messages from queue: {settings.QUEUE_NAME}")

        # Dont send messages if im processing something, im busy bro
        self.channel.basic_qos(prefetch_count=1)

        # Set up consumer
        self.channel.basic_consume(
            queue=settings.QUEUE_NAME,
            on_message_callback=self.callback,
            auto_ack=False,  # Manual acknowledgment for reliability
        )

        logger.info("Waiting for messages. To exit press CTRL+C")
        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            logger.info("Stopping consumer...")
            self.channel.stop_consuming()
        finally:
            self.connection.close()
            logger.info("Connection closed")


if __name__ == "__main__":
    consumer = MessageConsumer()
    consumer.start_consuming()
