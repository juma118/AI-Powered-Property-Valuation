"""Celery application for the proptech background workers.

Broker and result backend both point at ``settings.redis_url`` (Redis).
Run a worker with::

    celery -A app.workers.celery_app:celery_app worker --loglevel=info

Run the beat scheduler with::

    celery -A app.workers.celery_app:celery_app beat --loglevel=info
"""

from __future__ import annotations

from celery import Celery
from celery.schedules import crontab

from app.config import settings

celery_app = Celery(
    "proptech",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    result_expires=3600,
    broker_connection_retry_on_startup=True,
)

# Periodic schedule for the ETL pipeline. Refresh popular markets nightly and
# warm the read caches more frequently.
celery_app.conf.beat_schedule = {
    "refresh-popular-markets-nightly": {
        "task": "app.workers.tasks.run_pipeline_task",
        "schedule": crontab(hour=3, minute=0),
        "kwargs": {
            "cities": [
                ["Austin", "TX"],
                ["Denver", "CO"],
                ["Miami", "FL"],
                ["Seattle", "WA"],
            ]
        },
    },
    "warm-cache-hourly": {
        "task": "app.workers.tasks.warm_cache",
        "schedule": crontab(minute=0),
    },
}

__all__ = ["celery_app"]
