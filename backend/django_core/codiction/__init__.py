"""
Codiction Django project.

Celery is auto-imported so @shared_task decorators work correctly.
"""

from .celery import celery as celery_app

__all__ = ("celery_app",)