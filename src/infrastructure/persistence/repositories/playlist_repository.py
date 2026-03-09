from typing import Optional

from src.infrastructure.persistence.orm_models import PlaylistORM
from src.infrastructure.persistence.database import get_db
from src.logger.logger import setup_logger

logger = setup_logger(__name__)


class PlaylistRepository:

    def save(self, playlist: PlaylistORM) -> None:
        """Insert or update a playlist."""
        with get_db() as db:
            db.merge(playlist)   # merge = insert if not exists, update if exists
            logger.info(f"Saved playlist: {playlist.id}")

    def get_by_id(self, playlist_id: str) -> Optional[PlaylistORM]:
        """Fetch a playlist by its YouTube playlist ID."""
        with get_db() as db:
            return db.get(PlaylistORM, playlist_id)

    def exists(self, playlist_id: str) -> bool:
        """Check if a playlist already exists in the database."""
        with get_db() as db:
            return db.get(PlaylistORM, playlist_id) is not None