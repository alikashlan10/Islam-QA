# from src.infrastructure.celery.tasks.ingest_video_task import ingest_video_task

# ingest_video_task.delay("https://youtu.be/OYDXH_uUy8Y?si=HAXEoIqg1JfEcPLd")

from src.infrastructure.celery.tasks.ingest_playlist_task import ingest_playlist_task
ingest_playlist_task.delay("https://www.youtube.com/playlist?list=PL6C71skKjoGsHYPmniKWbQV7jKMFjYVdz" , 5)