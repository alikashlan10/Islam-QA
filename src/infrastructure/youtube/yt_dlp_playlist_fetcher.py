import yt_dlp

from src.application.interfaces.playlist_fetcher import PlaylistFetcher
from src.domain.models.playlist_metadata import PlaylistMetadata
from src.logger.logger import setup_logger

logger = setup_logger(__name__)


class YtDlpPlaylistFetcher(PlaylistFetcher):

    def fetch(self, playlist_url: str) -> PlaylistMetadata:
        logger.info(f"Fetching playlist info from: {playlist_url}")

        ydl_opts = {
            "quiet": True,
            "extract_flat": True,
            "skip_download": True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(playlist_url, download=False)

        video_urls = [
            entry["url"]
            for entry in info["entries"]
            if entry.get("url")
        ]

        logger.info(f"Found {len(video_urls)} videos in playlist: {info.get('title')}")

        return PlaylistMetadata(
            id=info.get("id"),
            title=info.get("title"),
            channel_name=info.get("uploader"),
            channel_url=info.get("uploader_url"),
            video_urls=video_urls,
        )