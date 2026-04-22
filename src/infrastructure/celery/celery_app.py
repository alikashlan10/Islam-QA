from celery import Celery
from src.config import AppConfig

config = AppConfig()

from celery.signals import setup_logging

@setup_logging.connect
def config_loggers(*args, **kwargs):
    pass  # disable Celery's logging setup entirely — use yours only

celery_app = Celery(
    "islam_qa",
    broker=config.REDIS_URL,      # redis://localhost:6379/0
    backend=config.REDIS_URL,
    include=[
        "src.infrastructure.celery.tasks.ingest_video_task",
        "src.infrastructure.celery.tasks.ingest_playlist_task",
        "src.infrastructure.celery.tasks.embed_transcripts_task"
    ]
)

celery_app.conf.worker_hijack_root_logger = False  # don't hijack root logger
celery_app.conf.worker_redirect_stdouts  = False   # don't redirect stdout

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_track_started=True,
    task_time_limit=60 * 180,  # 180(3hr) min max per task
)