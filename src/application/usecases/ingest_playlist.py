"""
IngestPlaylist Use Case
========================
Fetches a playlist and ingests each video using IngestVideoUseCase.
Skips failed videos and continues to the next one.
"""

from src.application.interfaces.playlist_fetcher import PlaylistFetcher
from src.application.mappers.playlist_mapper import PlaylistMapper
from src.application.usecases.ingest_video import IngestVideoUseCase
from src.infrastructure.persistence.repositories.playlist_repository import PlaylistRepository
from src.domain.enums.ingest_status import IngestStatus
from src.domain.models.ingest_result import PlaylistIngestResult
from src.logger.logger import setup_logger

logger = setup_logger(__name__)


class IngestPlaylistUseCase:

    def __init__(
        self,
        fetcher:           PlaylistFetcher,
        playlist_repo:     PlaylistRepository,
        ingest_video:      IngestVideoUseCase,
    ) -> None:
        self._fetcher       = fetcher
        self._playlist_repo = playlist_repo
        self._ingest_video  = ingest_video

    def execute(self, playlist_url: str, limit: int = None) -> PlaylistIngestResult:

        # fetch play list data
        playlist = self._fetcher.fetch(playlist_url)
        # mapping
        playlist_orm = PlaylistMapper.to_orm(playlist)
        # save to database 
        self._playlist_repo.save(playlist_orm)
        logger.info(f"Playlist saved: {playlist.id} — {len(playlist.video_urls)} videos")

        success = 0
        failed  = 0
        skipped = 0
        cntr    = 0

        for video_url in playlist.video_urls:

            if limit and cntr >= limit:
                break

            cntr += 1  

            try:
                result = self._ingest_video.execute(video_url, playlist)

                if result.status == IngestStatus.SUCCESS:
                    success += 1
                elif result.status == IngestStatus.SKIPPED:
                    skipped += 1
                else:
                    failed += 1

            except Exception as e:
                logger.error(f"Failed to ingest video {video_url}: {e}")
                failed += 1

        logger.info(
            f"Playlist ingestion complete: {playlist.id} — "
            f"{success} succeeded, {skipped} skipped, {failed} failed"
        )

        return PlaylistIngestResult(
            playlist_id = playlist.id,
            total       = cntr,
            success     = success,
            skipped     = skipped,
            failed      = failed,
        )