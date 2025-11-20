# Consumer Service

The consumer service is responsible for consuming weather data messages from RabbitMQ and forwarding them to the internal API for persistence.

## Features

- **Message Consumption**: Listens to the `weather` queue in RabbitMQ
- **API Integration**: Forwards messages to the internal API via HTTP POST
- **Error Handling**: Robust error handling with message acknowledgment
- **Retry Logic**: Failed messages are requeued for retry
- **Logging**: Comprehensive logging using loguru

## Configuration

The consumer uses environment variables for configuration (via `.env` file):

- `QUEUE_NAME`: RabbitMQ queue name (default: `weather`)
- `RABBIT_HOST`: RabbitMQ host (default: `localhost`)
- `API_URL`: Internal API endpoint (default: `http://localhost:8000/api/weather`)

## Running Locally

1. Install dependencies:
   ```bash
   uv sync
   ```

2. Run the consumer:
   ```bash
   uv run python -m consumer_app.message_consumer
   ```

## Running with Docker

The consumer is included in the docker-compose setup:

```bash
cd docker
docker-compose up consumer
```

## Message Flow

1. Consumer connects to RabbitMQ
2. Listens for messages on the `weather` queue
3. Receives a message
4. Sends the message data to the internal API via HTTP POST
5. Acknowledges the message if successful
6. Requeues the message if API call fails (for retry)

## Error Handling

- **JSON Decode Errors**: Malformed messages are rejected without requeue
- **API Errors**: Messages are rejected with requeue for retry
- **Unexpected Errors**: Messages are rejected with requeue for retry
