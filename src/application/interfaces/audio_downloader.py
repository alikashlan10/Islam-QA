from abc import ABC, abstractmethod
from src.domain.models.audio_metadata import AudioMetadata
from src.domain.models.playlist_metadata import PlaylistMetadata

class AudioDownloader(ABC):
    """
    Interface for downloading audio from a single video URL.
    Returns an AudioMetadata object — ready to be persisted.
    """
    @abstractmethod
    def download(self, playlistMetadata: PlaylistMetadata, output_dir: str, video_url: str = None) -> AudioMetadata:
        """
        Downloads audio from a video URL into output_dir.
        Returns AudioMetadata describing the downloaded file.
        """
        pass