from typing import Optional, List
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

  