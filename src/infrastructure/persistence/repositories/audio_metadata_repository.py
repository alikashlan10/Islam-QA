from typing import Optional, List

from sqlalchemy import and_

from src.infrastructure.persistence.orm_models import AudioMetadataORM
from src.infrastructure.persistence.database import get_db
from src.logger.logger import setup_logger

logger = setup_logger(__name__)


class AudioMetadataRepository:

    def save(self, audio: AudioMetadataORM) -> None:
        """Insert or update an audio metadata record."""
        with get_db() as db:
            db.merge(audio)
            logger.info(f"Saved audio metadata: {audio.id}")

    def get_by_id(self, video_id: str) -> Optional[AudioMetadataORM]:
        """Fetch audio metadata by YouTube video ID."""
        with get_db() as db:
            return db.get(AudioMetadataORM, video_id)

    def get_by_playlist(self, playlist_id: str) -> List[AudioMetadataORM]:
        """Fetch all audio files belonging to a playlist."""
        with get_db() as db:
            return (
                db.query(AudioMetadataORM)
                .filter(AudioMetadataORM.playlist_id == playlist_id)
                .all()
            )

    def get_unprocessed(self) -> List[AudioMetadataORM]:
        """
        Fetch all videos that haven't been transcribed yet.
        Used to resume a failed pipeline without reprocessing completed videos.
        """
        with get_db() as db:
            return (
                db.query(AudioMetadataORM)
                .filter(AudioMetadataORM.transcribed == False)
                .all()
            )

    def update_flags(
        self,
        video_id: str,
        transcribed: bool = None,
        qa_extracted: bool = None,
        embedded: bool = None,
    ) -> None:
        """
        Update pipeline tracking flags for a specific video.
        Only updates fields that are explicitly passed — ignores None values.
        """
        with get_db() as db:
            audio = db.get(AudioMetadataORM, video_id)
            if not audio:
                logger.warning(f"Audio metadata not found for video_id: {video_id}")
                return

            if transcribed  is not None: audio.transcribed  = transcribed
            if qa_extracted is not None: audio.qa_extracted = qa_extracted
            if embedded     is not None: audio.embedded     = embedded

            logger.info(f"Updated flags for video: {video_id}")