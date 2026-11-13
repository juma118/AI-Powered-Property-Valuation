"""Background workers, Celery tasks, and the data pipeline (ETL).
"""

from .celery_app import celery_app

__all__ = ["celery_app"]
