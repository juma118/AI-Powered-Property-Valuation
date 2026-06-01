"""Background workers, Celery tasks, and the data pipeline (ETL).

The pipeline stages are:

    Pull -> Normalize -> Store -> Geocode -> Embed -> Analyze

- Pull/Normalize/Store/Geocode: ``property_service.ingest_search`` (uses the
  RentCast client + enrichment/geocoding service).
- Embed: ``property_service.generate_embeddings`` (OpenAI or deterministic
  mock fallback).
- Analyze: ``ai_service`` / ``property_service.generate_analysis`` producing the
  persisted ``analyses`` rows.

The Celery app lives in ``celery_app``; the schedulable tasks in ``tasks``; the
orchestrated ETL in ``pipeline``.
"""

from .celery_app import celery_app

__all__ = ["celery_app"]
