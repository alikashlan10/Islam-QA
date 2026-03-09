# src/tests/integration/infrastructure/test_yt_dlp_audio_downloader_integration.py

import os
import pytest
from src.infrastructure.youtube.yt_dlp_audio_downloader import YtDlpAudioDownloader
from src.infrastructure.youtube.yt_dlp_playlist_fetcher import YtDlpPlaylistFetcher
from src.domain.models.audio_metadata import AudioMetadata
from src.logger.logger import setup_logger

logger = setup_logger(__name__)


OUTPUT_DIR = "src/tests/fixtures/downloads"

# a short public Arabic video
TEST_VIDEO_URL = "https://youtu.be/opJL0IFE6OY?si=ewPjFoh6icNgnwTQ"

# a short public Arabic playlist
TEST_PLAYLIST_URL = "https://www.youtube.com/playlist?list=PLx3Fh1kiMbreHf42n_0pkM7vP26q1TylO"


@pytest.mark.integration
def test_real_single_video_download():
    """
    Downloads a real single video with no playlist context.
    Verifies file lands in single_videos/ subdirectory.
    """
    downloader = YtDlpAudioDownloader()
    result = downloader.download(TEST_VIDEO_URL, OUTPUT_DIR)

    try:
        assert isinstance(result, AudioMetadata)
        assert os.path.exists(result.file_path), f"File not found: {result.file_path}"
        assert result.file_name.endswith(".mp3")
        assert result.id != ""
        assert result.title != ""
        assert result.channel_name is not None
        assert result.duration_seconds > 0
        assert result.playlist_url is None
        assert result.transcribed   == False
        assert result.qa_extracted  == False
        assert result.embedded      == False

        # verify directory structure
        assert "single_videos" in result.file_path

    finally:
        # always cleanup even if assertions fail
        if os.path.exists(result.file_path):
            os.remove(result.file_path)


@pytest.mark.integration
def test_real_playlist_video_download():
    """
    Fetches a real playlist then downloads its first video.
    Verifies file lands in {title}_{id}/ subdirectory.
    """
    fetcher    = YtDlpPlaylistFetcher()
    downloader = YtDlpAudioDownloader()

    playlist = fetcher.fetch(TEST_PLAYLIST_URL)

    # only download first video to keep test fast
    result = downloader.download(playlist.video_urls[0], OUTPUT_DIR, playlist=playlist)

    try:
        assert isinstance(result, AudioMetadata)
        assert os.path.exists(result.file_path), f"File not found: {result.file_path}"
        assert result.playlist_url == playlist.id

        # verify subdirectory contains playlist id
        assert playlist.id in result.file_path

    finally:
        if os.path.exists(result.file_path):
            logger.info(f"File exists at {result.file_path}")
            logger.info(f"file title : {result.title}")