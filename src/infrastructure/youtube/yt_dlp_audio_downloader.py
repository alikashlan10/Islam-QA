import os
import uuid
from datetime import datetime, timezone
import shutil
import re
import yt_dlp

from src.application.interfaces.audio_downloader import AudioDownloader
from src.domain.models.audio_metadata import AudioMetadata
from src.logger.logger import setup_logger
from src.domain.models.playlist_metadata import PlaylistMetadata

logger = setup_logger(__name__)


class YtDlpAudioDownloader(AudioDownloader):
    """
    Downloads audio from a YouTube video using yt-dlp.
    Extracts all available metadata and returns an AudioMetadata object.
    """

    def download(
    self,
    video_url: str,
    output_dir: str,
    playlist: PlaylistMetadata = None,
    ) -> AudioMetadata:

        logger.info(f"Downloading audio from: {video_url}")

        # guard against missing ffmpeg
        if not shutil.which("ffmpeg"):
            raise EnvironmentError("FFmpeg is not installed. Required for audio conversion.")

        # build subdirectory based on playlist or default
        if playlist:
            sanitized_title = self._sanitize_dirname(playlist.title)
            subdir = f"{sanitized_title}_{playlist.id}"
        else:
            subdir = "single_videos"

        actual_output_dir = os.path.join(output_dir, subdir)
        os.makedirs(actual_output_dir, exist_ok=True)

        ydl_opts = {
            "format": "bestaudio/best",
            "quiet": True,
            "outtmpl": os.path.join(actual_output_dir, "%(id)s.%(ext)s"),  # just youtube id
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)

        youtube_video_id = info.get("id")
        file_name = f"{youtube_video_id}.mp3"
        file_path = os.path.join(actual_output_dir, file_name)

        upload_date = self._parse_upload_date(info.get("upload_date"))

        logger.info(f"Download complete: {file_name}")

        return AudioMetadata(
            id=youtube_video_id,
            title=info.get("title", "untitled"),
            file_name=file_name,
            file_path=file_path,

            video_url=video_url,
            playlist_url=playlist.id if playlist else None,
            channel_name=info.get("uploader"),
            channel_url=info.get("uploader_url"),

            duration_seconds=info.get("duration"),
            upload_date=upload_date,
            description=info.get("description"),
            thumbnail_url=info.get("thumbnail"),
            language=info.get("language"),
            tags=info.get("tags") or [],

            downloaded_at=datetime.now(timezone.utc),
            transcribed=False,
            qa_extracted=False,
            embedded=False,
        )

    @staticmethod
    def _sanitize_dirname(title: str) -> str:
        """
        Removes characters invalid in directory names.
        Keeps Arabic characters intact, removes filesystem-unsafe chars.
        """
        sanitized = re.sub(r'[\\/*?:"<>|]', "", title)
        sanitized = sanitized.strip().replace(" ", "_")
        return sanitized[:50]  # cap at 50 chars for directory names

    @staticmethod
    def _parse_upload_date(date_str: str) -> datetime | None:
        if not date_str:
            return None
        try:
            return datetime.strptime(date_str, "%Y%m%d").replace(tzinfo=timezone.utc)
        except ValueError:
            return None