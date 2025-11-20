import json
from loguru import logger
import requests
from consumer_app.config import settings
import pika


class MessageConsumer:
    def __init__(self):
        logger.info("Connecting to RabbitMQ")
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=settings.RABBIT_HOST)
        )
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue=settings.QUEUE_NAME)
        logger.success("Connected to RabbitMQ")

    def callback(self, ch, method, properties, body):
        """Callback function to process messages from the queue"""
        try:
            logger.info("Received message from RabbitMQ")
            logger.debug(f"Message body: {body}")
            
            # Parse the message
            message_data = json.loads(body)
            
            # Send to internal API
            logger.info(f"Sending data to API: {settings.API_URL}")
            response = requests.post(
                settings.API_URL,
                json=message_data,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            response.raise_for_status()
            
            logger.success(f"Data successfully sent to API. Status: {response.status_code}")
            
            # Acknowledge the message
            ch.basic_ack(delivery_tag=method.delivery_tag)
            logger.info("Message acknowledged")
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode message: {e}")
            # Reject and don't requeue malformed messages
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send data to API: {e}")
            # Reject and requeue for retry
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
            
        except Exception as e:
            logger.error(f"Unexpected error processing message: {e}")
            # Reject and requeue for retry
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    def start_consuming(self):
        """Start consuming messages from the queue"""
        logger.info(f"Starting to consume messages from queue: {settings.QUEUE_NAME}")
        
        # Set QoS to process one message at a time
        self.channel.basic_qos(prefetch_count=1)
        
        # Set up consumer
        self.channel.basic_consume(
            queue=settings.QUEUE_NAME,
            on_message_callback=self.callback,
            auto_ack=False  # Manual acknowledgment for reliability
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
