import os
from celery import Celery
from app.core.config import settings

# Initialize the Celery Application (The Worker)
# We name the worker 'moment_finder_worker' and point it to our Redis Broker
celery_app = Celery(
    "moment_finder_worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_BROKER_URL, # We can use Redis to store the results too
    include=["app.worker.tasks"] # Tell Celery where to look for the @task functions
)

# Optional configuration to make Celery behave cleanly with JSON
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)
