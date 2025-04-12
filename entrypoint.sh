#!/bin/sh

# Exit immediately if a command exits with a non-zero status
set -e

# Start the Django development server
echo "Starting the server..."
python3 manage.py runserver 0.0.0.0:8000

echo "Listening on Port 8000"
exec "$@"