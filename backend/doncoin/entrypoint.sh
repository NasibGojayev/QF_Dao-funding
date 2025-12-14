#!/bin/sh

# Wait for database
if [ -n "$DB_HOST" ]
then
    echo "Waiting for postgres at $DB_HOST:$DB_PORT..."

    while ! nc -z $DB_HOST $DB_PORT; do
      sleep 0.1
    done

    echo "PostgreSQL started"
fi

# Run migrations
python manage.py migrate

# Start the application
# If we receive a command, run it, otherwise default to runserver
exec "$@"
