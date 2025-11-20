# Project Agents

This document defines the agents (services) within the event-driven pipeline.

## 1. Producer
- **Role**: Data Ingestion
- **Description**: Fetches weather data from the OpenWeather API and publishes it to the message queue.
- **Inputs**: OpenWeather API (HTTP)
- **Outputs**: RabbitMQ (Queue: `weather_data`)
- **Status**: Implemented (`src/producer`)

## 2. Consumer
- **Role**: Data Processing
- **Description**: Consumes messages from RabbitMQ and sends them to the internal API.
- **Inputs**: RabbitMQ
- **Outputs**: Internal API (HTTP POST)
- **Status**: Planned

## 3. API
- **Role**: Data Persistence
- **Description**: Receives data from the Consumer and stores it in the database.
- **Inputs**: HTTP Requests (from Consumer)
- **Outputs**: Database (Write)
- **Status**: Planned

## 4. Dashboard
- **Role**: Visualization
- **Description**: Fetches data from the API and displays it to the user.
- **Inputs**: Internal API (HTTP GET)
- **Outputs**: User Interface
- **Status**: Planned
