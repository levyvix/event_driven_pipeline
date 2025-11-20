<!-- OPENSPEC:START -->
# OpenSpec Instructions

These instructions are for AI assistants working in this project.

Always open `@/openspec/AGENTS.md` when the request:
- Mentions planning or proposals (words like proposal, spec, change, plan)
- Introduces new capabilities, breaking changes, architecture shifts, or big performance/security work
- Sounds ambiguous and you need the authoritative spec before coding

Use `@/openspec/AGENTS.md` to learn:
- How to create and apply change proposals
- Spec format and conventions
- Project structure and guidelines

Keep this managed block so 'openspec update' can refresh the instructions.

<!-- OPENSPEC:END -->

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
- **Status**: Implemented (`src/consumer`)

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
