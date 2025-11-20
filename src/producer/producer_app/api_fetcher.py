import json
from loguru import logger
import requests
from producer_app.config import settings

import pika


class ApiFetcher:
    def __init__(self):
        logger.info("Connecting to RabbitMQ")
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=settings.RABBIT_HOST)
        )
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue=settings.QUEUE_NAME)
        logger.success("Connected to RabbitMQ")

    def get_data(self):
        logger.info("About to fetch data from API")
        response = requests.get(
            settings.BASE_URL,
            params={
                "q": f"{settings.LAT},{settings.LON}",
                "key": settings.API_KEY,
            },
        )
        logger.info("Received data from API")
        response.raise_for_status()
        return response

    def send_data(self, data):
        logger.info("About to send data to RabbitMQ")
        logger.debug(data.json())
        self.channel.basic_publish(
            exchange="", routing_key=settings.QUEUE_NAME, body=json.dumps(data.json())
        )
        logger.success("Data sent to RabbitMQ")


import time
from datetime import datetime, timedelta

if __name__ == "__main__":
    api_fetcher = ApiFetcher()
    while True:
        try:
            api_fetcher.send_data(api_fetcher.get_data())
        except Exception as e:
            logger.error(f"An error occurred: {e}")
        
        now = datetime.now()
        next_hour = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
        seconds_to_sleep = (next_hour - now).total_seconds()
        
        logger.info(f"Sleeping for {seconds_to_sleep:.2f} seconds until {next_hour}...")
        time.sleep(seconds_to_sleep)
