"""
IngestVideo Use Case
=====================
Downloads, transcribes, and extracts QA pairs from a single video.
Supports partial resume:
    - transcribed=True  and qa_extracted=True  → skip entirely
    - transcribed=True  and qa_extracted=False → skip download + transcribe, only extract QA
    - transcribed=False                        → full pipeline
"""

from src.application.interfaces.audio_downloader import AudioDownloader
from src.application.interfaces.transcriber import Transcriber
from src.application.interfaces.qa_extractor import QAExtractor
from src.application.mappers.audio_metadata_mapper import AudioMetadataMapper
from src.application.mappers.transcript_mapper import TranscriptMapper
from src.application.mappers.qa_pair_mapper import QAPairMapper
from src.domain.models.playlist_metadata import PlaylistMetadata
from src.infrastructure.persistence.repositories.audio_metadata_repository import AudioMetadataRepository
from src.infrastructure.persistence.repositories.transcript_repository import TranscriptRepository
from src.infrastructure.persistence.repositories.qa_pair_repository import QAPairRepository
from src.domain.models.ingest_result import IngestResult
from src.domain.enums.ingest_status import IngestStatus
from src.config import AppConfig
from src.logger.logger import setup_logger

logger = setup_logger(__name__)
config = AppConfig()


class IngestVideoUseCase:

    def __init__(
        self,
        downloader:      AudioDownloader,
        transcriber:     Transcriber,
        extractor:       QAExtractor,
        audio_repo:      AudioMetadataRepository,
        transcript_repo: TranscriptRepository,
        qa_repo:         QAPairRepository,
    ) -> None:
        self._downloader      = downloader
        self._transcriber     = transcriber
        self._extractor       = extractor
        self._audio_repo      = audio_repo
        self._transcript_repo = transcript_repo
        self._qa_repo         = qa_repo

    def execute(
        self,
        video_url: str,
        playlist:  PlaylistMetadata = None,
    ) -> IngestResult:

        logger.info(f"Starting ingestion for video: {video_url}")

        # ── Step 1: Check existing state ──────────────────────────────────────

        # extract video id from url to check db
        video_id = self._extract_video_id(video_url)
        existing = self._audio_repo.get_by_id(video_id)

        if existing and existing.transcribed and existing.qa_extracted:
            logger.info(f"Video already fully processed, skipping: {video_id}")
            return IngestResult(video_id=video_id, status=IngestStatus.SKIPPED)
        


        # ── Step 2: Download ──────────────────────────────────────────────────

        if not existing:

            # download audio and get metadata
            logger.info(f"Downloading video: {video_url}")
            audioMetaData = self._downloader.download(
                video_url  = video_url,
                output_dir = config.AUDIO_OUTPUT_DIR,
                playlist   = playlist,
            )
            # mapping
            audio_orm = AudioMetadataMapper.to_orm(audioMetaData, playlist)
            # save to database
            self._audio_repo.save(audio_orm)
            logger.info(f"Audio saved: {audioMetaData.id}")

        else:
            # already downloaded — load from db
            audio_orm = existing
            logger.info(f"Audio already downloaded, loading from DB: {video_id}")



        # ── Step 3: Transcribe ────────────────────────────────────────────────

        if not audio_orm.transcribed:

            # transcribe audio
            logger.info(f"Transcribing audio: {audio_orm.file_path}")
            transcript = self._transcriber.transcribe(audio_orm.file_path)

            # save transcript
            transcript_orm = TranscriptMapper.to_orm(transcript, video_id=audio_orm.id)
            self._transcript_repo.save(transcript_orm)

            # uodate flags
            self._audio_repo.update_flags(audio_orm.id, transcribed=True)
            logger.info(f"Transcript saved for video: {audio_orm.id}")

        else:
            # already transcribed — load from db
            transcript_orm = self._transcript_repo.get_by_video_id(audio_orm.id)
            logger.info(f"Transcript already exists, loading from DB: {audio_orm.id}")



        # ── Step 4: Extract QA ────────────────────────────────────────────────

        if not audio_orm.qa_extracted:

            # extract qa pairs
            logger.info(f"Extracting QA pairs for video: {audio_orm.id}")
            qa_pairs = self._extractor.extract(transcript_orm.full_text)

            # mapping
            qa_pairs_orm = [
                QAPairMapper.to_orm(qa, audio_orm.id, transcript_orm.id)
                for qa in qa_pairs
            ]

            # save in database
            self._qa_repo.save_batch(qa_pairs_orm)

            # updatae flags
            self._audio_repo.update_flags(audio_orm.id, qa_extracted=True)
            logger.info(f"Saved {len(qa_pairs_orm)} QA pairs for video: {audio_orm.id}")

        logger.info(f"Ingestion complete for video: {audio_orm.id}")

        # return success
        return IngestResult(video_id=video_id, status=IngestStatus.SUCCESS)

    @staticmethod
    def _extract_video_id(video_url: str) -> str:
        """
        Extracts YouTube video ID from URL.
        https://www.youtube.com/watch?v=dQw4w9WgXcQ → dQw4w9WgXcQ
        """
        from urllib.parse import urlparse, parse_qs
        parsed = urlparse(video_url)
        return parse_qs(parsed.query)["v"][0]
