#!/bin/bash

# Apply database migrations
echo "Applying migrations..."
python manage.py migrate

# Create superuser if not exists
python manage.py createsuperauto

# Start server
echo "Starting server..."
exec daphne -b 0.0.0.0 -p 8000 chat_project.asgi:application
