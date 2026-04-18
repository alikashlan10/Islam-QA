"""
IngestVideo Use Case
=====================
Downloads and transcribes from a single video.
Supports partial resume:
    - existing = true and transcribed=False    → skip download then transcribe
    - existing = False                        → full pipeline
"""

from src.application.interfaces.audio_downloader import AudioDownloader
from src.application.interfaces.transcriber import Transcriber
from src.application.mappers.audio_metadata_mapper import AudioMetadataMapper
from src.application.mappers.transcript_mapper import TranscriptMapper
from src.domain.models.playlist_metadata import PlaylistMetadata
from src.infrastructure.persistence.repositories.audio_metadata_repository import AudioMetadataRepository
from src.infrastructure.persistence.repositories.transcript_repository import TranscriptRepository
from src.domain.models.ingest_result import IngestResult
from src.domain.enums.ingest_status import IngestStatus
from src.config import AppConfig
from src.logger.logger import setup_logger

logger = setup_logger(__name__)
config = AppConfig()


class IngestVideoUseCase:

    def __init__(
        self,
        downloader: AudioDownloader,
        transcriber: Transcriber,
        audio_repo: AudioMetadataRepository,
        transcript_repo: TranscriptRepository,
    ) -> None:
        self._downloader = downloader
        self._transcriber = transcriber
        self._audio_repo = audio_repo
        self._transcript_repo = transcript_repo

    def execute(self, video_url: str, playlist: PlaylistMetadata = None) -> IngestResult:

        logger.info(f"Starting ingestion for video: {video_url}")

        video_id = self._extract_video_id(video_url)

        # ── Step 1: Check existing audio ───────────────────────────────
        audio = self._audio_repo.get_by_id(video_id)

        # ── Step 2: Check transcript (NEW SOURCE OF TRUTH) ─────────────
        transcript = self._transcript_repo.get_by_video_id(video_id)

        if transcript:
            logger.info(f"Transcript already exists for: {video_id}")
            return IngestResult(video_id=video_id, status=IngestStatus.SKIPPED)

        # ── Step 3: Download audio if needed ────────────────────────────
        if not audio:

            logger.info(f"Downloading video: {video_url}")

            audio_meta = self._downloader.download(
                video_url=video_url,
                output_dir=config.AUDIO_OUTPUT_DIR,
                playlist=playlist,
            )

            audio_orm = AudioMetadataMapper.to_orm(audio_meta, playlist)
            self._audio_repo.save(audio_orm)

            logger.info(f"Audio saved: {video_id}")

        else:
            audio_orm = audio
            logger.info(f"Audio already exists: {video_id}")

        # ── Step 4: Transcribe ─────────────────────────────────────────
        logger.info(f"Transcribing audio: {audio_orm.file_path}")

        transcript_obj = self._transcriber.transcribe(audio_orm.file_path)

        transcript_orm = TranscriptMapper.to_orm(
            transcript_obj,
            video_id=audio_orm.id
        )

        self._transcript_repo.save(transcript_orm)

        logger.info(f"Transcript saved for video: {audio_orm.id}")

        # ── Step 5: Return result ───────────────────────────────────────
        logger.info(f"Ingestion complete for video: {audio_orm.id}")

        return IngestResult(video_id=video_id, status=IngestStatus.SUCCESS)

    @staticmethod
    def _extract_video_id(video_url: str) -> str:
        from urllib.parse import urlparse, parse_qs
        parsed = urlparse(video_url)
        return parse_qs(parsed.query)["v"][0]