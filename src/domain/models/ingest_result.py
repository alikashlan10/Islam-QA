from src.domain.enums.ingest_status import IngestStatus
from dataclasses import dataclass

@dataclass
class IngestResult:
    video_id: str
    status:   IngestStatus
    message:  str = ""

    
@dataclass
class PlaylistIngestResult:
    playlist_id: str
    total:       int
    success:     int
    skipped:     int
    failed:      int