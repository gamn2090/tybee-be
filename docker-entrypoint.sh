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
if not User.objects.filter(is_superuser=True).exists():
    user=User.objects.create_superuser('admin','admin@yopmail.com', 'admin123')
    user.set_password('admin123')
    user.save()
    print('Superuser created')
EOF

# Start server (default: gunicorn)
exec gunicorn tybee_backend.wsgi:application --bind 0.0.0.0:8000
