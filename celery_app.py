# celery_app.py
from celery import Celery

celery_app = Celery(
    "worker",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0",
    include=["items.cron"],
)
celery_app.conf.timezone = "Asia/Kolkata"