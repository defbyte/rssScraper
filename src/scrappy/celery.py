import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scrappy.settings')

app = Celery('scrappy')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Setup the scheduled feed refreshes every 15 minutes
app.conf.beat_schedule = {
    'update-feeds-schedule': {
        'task': 'scrappy.feeds.tasks.update_feeds',
        'schedule': crontab(minute='*/2'),
    }
}
