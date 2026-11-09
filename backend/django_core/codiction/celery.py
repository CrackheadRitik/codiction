"""
Codiction — Celery configuration.

Loads Django settings automatically so tasks can access models.
"""

import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "codiction.settings.development")

# Create Celery app
celery = Celery("codiction")

# Read config from Django settings, prefix CELERY_
celery.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks from all installed apps
celery.autodiscover_tasks()


@celery.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task — prints request info."""
    print(f"Request: {self.request!r}")