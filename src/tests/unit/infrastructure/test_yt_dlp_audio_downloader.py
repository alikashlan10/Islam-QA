"""
Unit Tests for YtDlpAudioDownloader
=====================================
Run with: pytest src/tests/unit/infrastructure/test_yt_dlp_audio_downloader.py -v
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone

from src.infrastructure.youtube.yt_dlp_audio_downloader import YtDlpAudioDownloader
from src.domain.models.audio_metadata import AudioMetadata
from src.domain.models.playlist_metadata import PlaylistMetadata


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_mock_info(
    title: str = "Test Video Title",
    video_id: str = "dQw4w9WgXcQ",
    uploader: str = "Test Channel",
    uploader_url: str = "https://youtube.com/@testchannel",
    duration: float = 120.0,
    upload_date: str = "20240101",
    description: str = "Test description",
    thumbnail: str = "https://img.youtube.com/test.jpg",
    language: str = "ar",
    tags: list = None,
) -> dict:
    return {
        "id":           video_id,
        "title":        title,
        "uploader":     uploader,
        "uploader_url": uploader_url,
        "duration":     duration,
        "upload_date":  upload_date,
        "description":  description,
        "thumbnail":    thumbnail,
        "language":     language,
        "tags":         tags or ["tag1", "tag2"],
    }


def make_mock_playlist(
    id: str = "PLxxxxxxxxxxxxxxxx",
    title: str = "شرح الميراث",
    channel_name: str = "قناة العلم",
    channel_url: str = "https://youtube.com/@testchannel",
) -> PlaylistMetadata:
    return PlaylistMetadata(
        id=id,
        title=title,
        channel_name=channel_name,
        channel_url=channel_url,
        video_urls=["https://youtube.com/watch?v=dQw4w9WgXcQ"],
    )


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def downloader():
    return YtDlpAudioDownloader()


@pytest.fixture
def mock_yt_dlp():
    with patch("src.infrastructure.youtube.yt_dlp_audio_downloader.yt_dlp.YoutubeDL") as mock_class:
        mock_instance = MagicMock()
        mock_class.return_value.__enter__.return_value = mock_instance
        mock_class.return_value.__exit__.return_value = None
        yield mock_instance


@pytest.fixture
def mock_ffmpeg():
    with patch("src.infrastructure.youtube.yt_dlp_audio_downloader.shutil.which", return_value="/usr/bin/ffmpeg"):
        yield


@pytest.fixture
def mock_makedirs():
    with patch("src.infrastructure.youtube.yt_dlp_audio_downloader.os.makedirs"):
        yield


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestDownloadHappyPath:

    def test_returns_audio_metadata_object(self, downloader, mock_yt_dlp, mock_ffmpeg, mock_makedirs):
        mock_yt_dlp.extract_info.return_value = make_mock_info()
        result = downloader.download("https://youtube.com/watch?v=dQw4w9WgXcQ", "/tmp/audio")
        assert isinstance(result, AudioMetadata)

    def test_id_is_youtube_video_id(self, downloader, mock_yt_dlp, mock_ffmpeg, mock_makedirs):
        """id field should be the YouTube video ID, not a UUID."""
        mock_yt_dlp.extract_info.return_value = make_mock_info(video_id="dQw4w9WgXcQ")
        result = downloader.download("https://youtube.com/watch?v=dQw4w9WgXcQ", "/tmp/audio")
        assert result.id == "dQw4w9WgXcQ"

    def test_file_name_is_youtube_id_only(self, downloader, mock_yt_dlp, mock_ffmpeg, mock_makedirs):
        """File name should be just {youtube_id}.mp3 — no UUID suffix."""
        mock_yt_dlp.extract_info.return_value = make_mock_info(video_id="dQw4w9WgXcQ")
        result = downloader.download("https://youtube.com/watch?v=dQw4w9WgXcQ", "/tmp/audio")
        assert result.file_name == "dQw4w9WgXcQ.mp3"

    def test_metadata_fields_mapped_correctly(self, downloader, mock_yt_dlp, mock_ffmpeg, mock_makedirs):
        mock_yt_dlp.extract_info.return_value = make_mock_info(
            title="شرح الميراث",
            uploader="قناة العلم",
            duration=300.0,
            upload_date="20230615",
            language="ar",
            tags=["فقه", "ميراث"],
        )
        result = downloader.download("https://youtube.com/watch?v=dQw4w9WgXcQ", "/tmp/audio")
        assert result.title            == "شرح الميراث"
        assert result.channel_name     == "قناة العلم"
        assert result.duration_seconds == 300.0
        assert result.language         == "ar"
        assert result.tags             == ["فقه", "ميراث"]

    def test_upload_date_parsed_correctly(self, downloader, mock_yt_dlp, mock_ffmpeg, mock_makedirs):
        """yt-dlp returns upload_date as YYYYMMDD — verify it's parsed to datetime."""
        mock_yt_dlp.extract_info.return_value = make_mock_info(upload_date="20230615")
        result = downloader.download("https://youtube.com/watch?v=dQw4w9WgXcQ", "/tmp/audio")
        assert result.upload_date == datetime(2023, 6, 15, tzinfo=timezone.utc)

    def test_downloaded_at_is_set(self, downloader, mock_yt_dlp, mock_ffmpeg, mock_makedirs):
        """downloaded_at should be set to current UTC time."""
        mock_yt_dlp.extract_info.return_value = make_mock_info()
        before = datetime.now(timezone.utc)
        result = downloader.download("https://youtube.com/watch?v=dQw4w9WgXcQ", "/tmp/audio")
        after  = datetime.now(timezone.utc)
        assert before <= result.downloaded_at <= after

    def test_pipeline_tracking_fields_default_to_false(self, downloader, mock_yt_dlp, mock_ffmpeg, mock_makedirs):
        """A freshly downloaded audio should not be marked as processed yet."""
        mock_yt_dlp.extract_info.return_value = make_mock_info()
        result = downloader.download("https://youtube.com/watch?v=dQw4w9WgXcQ", "/tmp/audio")
        assert result.transcribed  == False
        assert result.qa_extracted == False
        assert result.embedded     == False


class TestDownloadDirectoryStructure:

    def test_single_video_uses_default_subdirectory(self, downloader, mock_yt_dlp, mock_ffmpeg, mock_makedirs):
        """When no playlist is provided, file should be inside single_videos/ subdirectory."""
        mock_yt_dlp.extract_info.return_value = make_mock_info()
        result = downloader.download("https://youtube.com/watch?v=dQw4w9WgXcQ", "/tmp/audio")
        assert "single_videos" in result.file_path

    def test_playlist_creates_titled_subdirectory(self, downloader, mock_yt_dlp, mock_ffmpeg, mock_makedirs):
        """
        When playlist is provided, file should be inside
        {sanitized_title}_{playlist_id}/ subdirectory.
        """
        mock_yt_dlp.extract_info.return_value = make_mock_info()
        playlist = make_mock_playlist(id="PLxxxxxxxxxxxxxxxx", title="شرح الميراث")

        result = downloader.download(
            "https://youtube.com/watch?v=dQw4w9WgXcQ",
            "/tmp/audio",
            playlist=playlist,
        )

        assert "PLxxxxxxxxxxxxxxxx" in result.file_path
        assert "شرح_الميراث" in result.file_path

    def test_file_path_ends_with_file_name(self, downloader, mock_yt_dlp, mock_ffmpeg, mock_makedirs):
        """file_path should always end with the file_name."""
        mock_yt_dlp.extract_info.return_value = make_mock_info(video_id="dQw4w9WgXcQ")
        result = downloader.download("https://youtube.com/watch?v=dQw4w9WgXcQ", "/tmp/audio")
        assert result.file_path.endswith(result.file_name)


class TestDownloadPlaylistHandling:

    def test_playlist_url_stores_playlist_id(self, downloader, mock_yt_dlp, mock_ffmpeg, mock_makedirs):
        """playlist_url in AudioMetadata should store the playlist ID, not the full URL."""
        mock_yt_dlp.extract_info.return_value = make_mock_info()
        playlist = make_mock_playlist(id="PLxxxxxxxxxxxxxxxx")

        result = downloader.download(
            "https://youtube.com/watch?v=dQw4w9WgXcQ",
            "/tmp/audio",
            playlist=playlist,
        )

        assert result.playlist_url == "PLxxxxxxxxxxxxxxxx"

    def test_playlist_url_is_none_for_single_video(self, downloader, mock_yt_dlp, mock_ffmpeg, mock_makedirs):
        """When no playlist is provided, playlist_url should be None."""
        mock_yt_dlp.extract_info.return_value = make_mock_info()
        result = downloader.download("https://youtube.com/watch?v=dQw4w9WgXcQ", "/tmp/audio")
        assert result.playlist_url is None


class TestDownloadEdgeCases:

    def test_missing_upload_date_returns_none(self, downloader, mock_yt_dlp, mock_ffmpeg, mock_makedirs):
        """Some videos don't have an upload date — should return None, not crash."""
        mock_yt_dlp.extract_info.return_value = make_mock_info(upload_date=None)
        result = downloader.download("https://youtube.com/watch?v=dQw4w9WgXcQ", "/tmp/audio")
        assert result.upload_date is None

    def test_invalid_upload_date_returns_none(self, downloader, mock_yt_dlp, mock_ffmpeg, mock_makedirs):
        """Malformed date string should return None instead of crashing."""
        mock_yt_dlp.extract_info.return_value = make_mock_info(upload_date="not-a-date")
        result = downloader.download("https://youtube.com/watch?v=dQw4w9WgXcQ", "/tmp/audio")
        assert result.upload_date is None

    def test_missing_tags_defaults_to_empty_list(self, downloader, mock_yt_dlp, mock_ffmpeg, mock_makedirs):
        """Videos without tags should return empty list, not None or crash."""
        info = make_mock_info()
        info["tags"] = None
        mock_yt_dlp.extract_info.return_value = info
        result = downloader.download("https://youtube.com/watch?v=dQw4w9WgXcQ", "/tmp/audio")
        assert result.tags == []


class TestDownloadErrorHandling:

    def test_raises_when_ffmpeg_not_installed(self, downloader):
        """If FFmpeg is not installed, should raise EnvironmentError before any download."""
        with patch("src.infrastructure.youtube.yt_dlp_audio_downloader.shutil.which", return_value=None):
            with pytest.raises(EnvironmentError, match="FFmpeg"):
                downloader.download("https://youtube.com/watch?v=dQw4w9WgXcQ", "/tmp/audio")

    def test_raises_on_yt_dlp_error(self, downloader, mock_yt_dlp, mock_ffmpeg, mock_makedirs):
        """If yt-dlp fails (private video, network error), exception should bubble up."""
        mock_yt_dlp.extract_info.side_effect = Exception("Video unavailable")
        with pytest.raises(Exception, match="Video unavailable"):
            downloader.download("https://youtube.com/watch?v=private", "/tmp/audio")