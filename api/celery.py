import os
from celery import Celery
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "api.settings.development")

app = Celery("rutineret")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Configure Celery to use Redis as broker
app.conf.update(
    broker_url=os.environ.get("REDIS_URL", "redis://localhost:6379/0"),
    result_backend=os.environ.get("REDIS_URL", "redis://localhost:6379/0"),
    accept_content=["json"],
    task_serializer="json",
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Celery Beat schedule
app.conf.beat_schedule = {
    "check-pending-alarms": {
        "task": "routines.tasks.check_pending_alarms",
        "schedule": 60.0,  # Run every minute
    },
    "cleanup-old-reminders": {
        "task": "routines.tasks.cleanup_old_reminders",
        "schedule": 3600.0,  # Run every hour
    },
}


@app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery connectivity."""
    print(f"Request: {self.request!r}")
