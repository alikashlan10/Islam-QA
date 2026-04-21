from src.infrastructure.celery.celery_app import celery_app

from src.application.usecases.ingest_video import IngestVideoUseCase

from src.infrastructure.persistence.repositories.audio_metadata_repository import AudioMetadataRepository
from src.infrastructure.persistence.repositories.transcript_repository import TranscriptRepository

from src.infrastructure.youtube.yt_dlp_audio_downloader import YtDlpAudioDownloader  # adjust to your implementation
from src.application.factories.transcriber_factory import TranscriberFactory      # adjust to your implementation

from src.domain.models.playlist_metadata import PlaylistMetadata
from src.config import AppConfig
 


@celery_app.task(name="ingest_video_task")
def ingest_video_task(video_url: str,job_id ,  playlist: dict = None):

    config = AppConfig()

    transcriber = TranscriberFactory().create(provider=config.TRANSCRIBER_PROVIDER)
    
    
    # ── rebuild use case (NO API LAYER) ─────────────────────────────
    use_case = IngestVideoUseCase(
        downloader=YtDlpAudioDownloader(),
        transcriber=transcriber,
        audio_repo=AudioMetadataRepository(),
        transcript_repo=TranscriptRepository(),
    )

    # convert dict → domain model if needed
    playlist_obj = PlaylistMetadata(**playlist) if playlist else None

    result = use_case.execute(
        video_url=video_url,
        playlist=playlist_obj
    )

    return {
        "video_id": result.video_id,
        "status": result.status.value
    }


