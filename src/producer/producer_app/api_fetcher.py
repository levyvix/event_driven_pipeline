from __future__ import annotations

import json
import time
from datetime import datetime, timedelta

import pika
import requests
from loguru import logger

from .config import settings

# API request timeout in seconds
REQUEST_TIMEOUT_SECONDS: int = 30


class ApiFetcher:
    """
    Fetches weather data from OpenWeather API and publishes to RabbitMQ.

    Retrieves current weather data from the OpenWeather API at configured
    coordinates and publishes the response to a RabbitMQ queue for
    downstream processing.
    """

    def __init__(self) -> None:
        """Initialize RabbitMQ connection and channel."""
        logger.info("Connecting to RabbitMQ")
        self.connection: pika.BlockingConnection = pika.BlockingConnection(
            pika.ConnectionParameters(host=settings.RABBIT_HOST)
        )
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue=settings.QUEUE_NAME)
        logger.success("Connected to RabbitMQ")

    def get_data(self) -> requests.Response:
        """
        Fetch current weather data from the OpenWeather API.

        Makes an HTTP GET request to the OpenWeather API with configured
        latitude, longitude, and API key. Includes a timeout to prevent
        indefinite hangs.

        Returns:
            Response object with weather data in JSON format

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
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        logger.info("Received data from API")
        response.raise_for_status()
        return response

    def send_data(self, data: requests.Response) -> None:
        """
        Publish weather data to RabbitMQ queue.

        Extracts JSON content from response and publishes as string
        to the configured queue for asynchronous processing.

        Args:
            data: Response object containing weather data

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

        logger.info(f"Sleeping for {seconds_to_sleep:.2f} seconds until {next_hour}...")
        time.sleep(seconds_to_sleep)
