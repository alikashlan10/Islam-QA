from typing import Optional , List
from datetime import datetime
from src.infrastructure.persistence.orm_models import TranscriptORM
from src.infrastructure.persistence.database import get_db
from src.logger.logger import setup_logger

logger = setup_logger(__name__)


class TranscriptRepository:

    def save(self, transcript: TranscriptORM) -> None:
        """Insert a new transcript."""
        with get_db() as db:
            db.add(transcript)
            logger.info(f"Saved transcript for video: {transcript.video_id}")

    def get_by_video_id(self, video_id: str) -> Optional[TranscriptORM]:
        """Fetch the transcript for a specific video."""
        with get_db() as db:
            return (
                db.query(TranscriptORM)
                .filter(TranscriptORM.video_id == video_id)
                .first()
            )

    def exists(self, video_id: str) -> bool:
        """
        Check if a transcript already exists for this video.
        Used to skip re-transcription if the pipeline is restarted.
        """
        with get_db() as db:
            return (
                db.query(TranscriptORM)
                .filter(TranscriptORM.video_id == video_id)
                .first()
            ) is not None
        
    def mark_as_embedded(self, video_id: str) -> None:
        """Mark transcript as embedded."""
        with get_db() as db:
            transcript = (
                db.query(TranscriptORM)
                .filter(TranscriptORM.video_id == video_id)
                .first()
            )

            if not transcript:
                logger.warning(f"No transcript found for video {video_id}")
                return

            transcript.embedded = True
            logger.info(f"Transcript marked as embedded for video: {video_id}")    



    def is_embedded(self, video_id: str) -> bool:
        """Check if transcript is already embedded."""
        with get_db() as db:
            transcript = (
                db.query(TranscriptORM.embedded)
                .filter(TranscriptORM.video_id == video_id)
                .first()
            )

            return transcript[0] if transcript else False
        
    def get_unembedded(self, limit: int = 100) -> list[TranscriptORM]:
        """
        Fetch a batch of unembedded transcripts.
        No offset is used — dataset shrinks as we mark rows embedded.
        """
        with get_db() as db:
            return (
                db.query(TranscriptORM)
                .filter(TranscriptORM.embedded == False)
                .order_by(TranscriptORM.created_at)
                .limit(limit)
                .all()
            )
        
    def get_all(self, limit: int = 100, offset: int = 0) -> list[TranscriptORM]:
        """
        Fetch all transcripts with simple pagination.
        Used for force re-embedding.
        """
        with get_db() as db:
            return (
                db.query(TranscriptORM)
                .order_by(TranscriptORM.created_at)
                .offset(offset)
                .limit(limit)
                .all()
            )