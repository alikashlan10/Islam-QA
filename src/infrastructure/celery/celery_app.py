from celery import Celery
from src.config import AppConfig

config = AppConfig()

celery_app = Celery(
    "islam_qa",
    broker=config.REDIS_URL,      # redis://localhost:6379/0
    backend=config.REDIS_URL,
    include=[
        "src.infrastructure.celery.tasks.ingest_video_task",
        "src.infrastructure.celery.tasks.ingest_playlist_task"
    ]
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_track_started=True,
    task_time_limit=60 * 30,  # 30 min max per task
)