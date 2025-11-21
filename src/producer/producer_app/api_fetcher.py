import json
import time
from datetime import datetime, timedelta

import pika  # rabbimq
import requests
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from .config import settings


class ApiFetcher:
    """
    Fetches weather data from OpenWeather API and publishes to RabbitMQ.

    Retrieves current weather data from the OpenWeather API at configured
    coordinates and publishes the response to a RabbitMQ queue for
    downstream processing.
    """

    def __init__(self) -> None:
        """Initialize RabbitMQ connection and channel."""
        self.connection, self.channel = self._connect_to_rabbitmq()
        self.timeout_seconds = 30

    @retry(
        stop=stop_after_attempt(30),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(pika.exceptions.AMQPConnectionError),
    )
    def _connect_to_rabbitmq(self) -> tuple[pika.BlockingConnection, pika.adapters.blocking_connection.BlockingChannel]:
        """
        Connect to RabbitMQ with exponential backoff retry.

        Attempts to establish a connection to RabbitMQ and declare the queue.
        Uses tenacity to retry with exponential backoff (1-10 seconds) up to 30 times.

        Returns:
            tuple: (pika.BlockingConnection, pika.adapters.blocking_connection.BlockingChannel)

        Raises:
            pika.exceptions.AMQPConnectionError: If all connection attempts fail
        """
        try:
            logger.info("Attempting to connect to RabbitMQ at {host}:{port}", host=settings.RABBIT_HOST, port=5672)
            connection: pika.BlockingConnection = pika.BlockingConnection(
                pika.ConnectionParameters(host=settings.RABBIT_HOST)
            )
            channel = connection.channel()
            channel.queue_declare(queue=settings.QUEUE_NAME)
            logger.success("Successfully connected to RabbitMQ")
            return connection, channel
        except pika.exceptions.AMQPConnectionError as e:
            logger.warning("Failed to connect to RabbitMQ: {error}", error=e)
            raise

    def get_data(self) -> requests.Response:
        """
        Fetch current weather data from the OpenWeather API.

        Makes an HTTP GET request to the OpenWeather API with configured
        latitude, longitude, and API key. Includes a timeout to prevent
        indefinite hangs.

        Raises:
            requests.HTTPError: If API returns an error status
            requests.Timeout: If request exceeds timeout
            requests.RequestException: For other request failures
        """
        logger.info("About to fetch data from API")
        response: requests.Response = requests.get(
            settings.BASE_URL,
            params={
                "q": f"{settings.LAT},{settings.LON}",
                "key": settings.API_KEY,
            },
            timeout=self.timeout_seconds,
        )
        logger.info("Received data from API")
        response.raise_for_status()
        return response

    def send_data(self, data: requests.Response) -> None:
        """
        Publish weather data to RabbitMQ queue.

        Extracts JSON content from response and publishes as string
        to the configured queue for asynchronous processing.

        Raises:
            Exception: If publishing fails
        """
        logger.info("About to send data to RabbitMQ")
        logger.debug(data.json())
        self.channel.basic_publish(
            exchange="", routing_key=settings.QUEUE_NAME, body=json.dumps(data.json())
        )
        logger.success("Data sent to RabbitMQ")


if __name__ == "__main__":
    api_fetcher = ApiFetcher()
    # Fetch data every hour, then sleep until the next "full" hour
    while True:
        try:
            api_fetcher.send_data(api_fetcher.get_data())
        except Exception as e:
            logger.error(f"An error occurred: {e}")

        now = datetime.now()
        next_hour = (now + timedelta(hours=1)).replace(
            minute=0, second=0, microsecond=0
        )
        seconds_to_sleep = (next_hour - now).total_seconds()

        logger.info(
            f"Sleeping for {seconds_to_sleep:.2f} seconds until {next_hour.strftime('%Y-%m-%d %H:%M:%S')}..."
        )
        time.sleep(seconds_to_sleep)
