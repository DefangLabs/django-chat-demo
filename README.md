# Django Real-Time Chat Application with Auto Mod

A modern real-time chat application built with Django, Channels, and WebSocket technology. Features include user authentication, real-time messaging, message moderation, and Docker support.

## Features

- Real-time messaging using WebSocket connections
- User authentication (register/login)
- Chat rooms
- Automatic message moderation system using NLTK
- Asynchronous task processing with Celery
- Docker support for development and production

## Tech Stack

- Django - Web framework
- Django Channels - WebSocket handling
- Celery - Background task processing
- Docker - Containerization
- PostgreSQL - Database
- Redis - Websocket and Message Queue broker

## Getting Started

### Development Setup

1. Clone the repository
2. Run the development environment:
   ```bash
   docker compose --env-file .env.dev -f compose.dev.yaml up --build
   ```
3. Access the application at http://localhost:8000

### Deploy to Defang Playground

1. Clone the repository
2. Run the production environment:
   ```bash
   defang config set DJANGO_SECRET_KEY
   defang config set POSTGRES_PASSWORD
   defang compose up
   ```

### Deploy to your own cloud account

1. Clone the repository
2. Configure your [cloud provider](https://docs.defang.io/docs/concepts/defang-byoc) (i.e. `export DEFANG_PROVIDER=aws,gcp,etc.`, add credentials, etc.)
3. Run the production environment:
   ```bash
   export DEFANG_PROVIDER=<your-provider-of-choice>
   defang config set DJANGO_SECRET_KEY
   defang config set POSTGRES_PASSWORD
   defang compose up
   ```


