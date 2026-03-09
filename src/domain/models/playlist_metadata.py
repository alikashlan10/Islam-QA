# domain/models/playlist_metadata.py

from pydantic import BaseModel
from typing import List

class PlaylistMetadata(BaseModel):
    id: str                  # YouTube playlist ID e.g. "PLxxxxxxxxxxxxxxxx"
    title: str               # playlist title e.g. "شرح الميراث"
    channel_name: str | None # uploader/channel name
    channel_url: str | None  # channel URL
    video_urls: List[str]    # all video URLs in the playlist