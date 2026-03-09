from abc import ABC, abstractmethod
from typing import List
from src.domain.models.playlist_metadata import PlaylistMetadata


class PlaylistFetcher(ABC):
    """
    Interface for fetching video URLs from a playlist.
    """
    @abstractmethod
    def fetch(self, playlist_url: str) -> PlaylistMetadata:
        """
        Given a playlist URL, returns a list of individual video URLs.
        """
        pass