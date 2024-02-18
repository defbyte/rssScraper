#!/bin/bash
echo "Hello from entrypoint"
cd /app/src/
echo "Activate virtualenv"
. /opt/venv/bin/activate

python manage.py migrate
python manage.py collectstatic --noinput

# Start Celery
/opt/venv/bin/celery -A scrappy worker -l info --detach
/opt/venv/bin/celery -A scrappy beat -l info --detach

# Start the Django app
/opt/venv/bin/gunicorn --worker-tmp-dir /dev/shm scrappy.wsgi:application --bind "0.0.0.0:8000"
