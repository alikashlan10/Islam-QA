from src.infrastructure.celery.celery_app import celery_app

from src.application.usecases.ingest_playlist import IngestPlaylistUseCase
from src.infrastructure.persistence.repositories.audio_metadata_repository import AudioMetadataRepository
from src.infrastructure.persistence.repositories.playlist_repository import PlaylistRepository
from src.infrastructure.persistence.repositories.transcript_repository import TranscriptRepository

from src.infrastructure.youtube.yt_dlp_playlist_fetcher import YtDlpPlaylistFetcher    # example
 
from src.application.usecases.ingest_video import IngestVideoUseCase

from src.infrastructure.persistence.repositories.audio_metadata_repository import AudioMetadataRepository
from src.infrastructure.persistence.repositories.transcript_repository import TranscriptRepository

from src.infrastructure.youtube.yt_dlp_audio_downloader import YtDlpAudioDownloader 
from src.application.factories.transcriber_factory import TranscriberFactory      
from src.domain.models.playlist_metadata import PlaylistMetadata
from src.config import AppConfig
 

@celery_app.task(name="ingest_playlist_task")
def ingest_playlist_task(playlist_url: str, limit: int = 10):
   
    config = AppConfig()
    transcriber = TranscriberFactory().create(provider=config.TRANSCRIBER_PROVIDER)

    # define ingest video usecase
    ingest_video_usecase = IngestVideoUseCase(
        downloader=YtDlpAudioDownloader(),
        transcriber=transcriber,
        audio_repo=AudioMetadataRepository(),
        transcript_repo=TranscriptRepository(),
    )

    use_case = IngestPlaylistUseCase(
        playlist_repo=PlaylistRepository(),
        ingest_video=ingest_video_usecase,
        fetcher=YtDlpPlaylistFetcher()
    )

    result = use_case.execute(
        playlist_url=playlist_url,
        limit=limit
    )

    return {
        "total": result.total,
        "success": result.success
    }