#!/bin/sh
# Entrypoint script for Django Docker container

set -e

echo "Starting Django application..."

# Wait for database to be ready
# echo "Waiting for database..."
# while ! nc -vz $DB_HOST $DB_PORT >/dev/null 2>&1; do
#   sleep 0.5
# done
# echo "Database started"
echo "Database Host: $DB_HOST"
echo "Database Port: $DB_PORT"
echo "Database Name: $DB_NAME"
echo "Database User: $DB_USER"

# Apply database migrations
python manage.py migrate --noinput

# Collect static files
python manage.py collectstatic --noinput

# Create superuser if not exists
python manage.py shell <<EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(phone_number="9999999999", is_superuser=True).exists():
    user = User.objects.create_superuser(phone_number="9999999999", password='admin123')
    print('Superuser created')
EOF

# Start server (default: gunicorn)
# Render (and most PaaS) assign the port to listen on via $PORT and route
# traffic to it — a hardcoded 8000 works in plain Docker/ECS but makes the
# service unreachable on Render. Falls back to 8000 for local `docker run`.
exec gunicorn tybee_backend.wsgi:application --bind 0.0.0.0:${PORT:-8000}
