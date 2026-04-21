from pydantic import BaseModel
from uuid import UUID
from datetime import datetime 

class IngestVideoRequest(BaseModel):
    video_url: str

class IngestPlaylistRequest(BaseModel):
    playlist_url: str
    limit: int 

class EmbedRequest(BaseModel):
    force: bool = False

class JobResponse(BaseModel):
    job_id: UUID
    status: str
    type: str


class JobProgress(BaseModel):
    id: UUID
    type: str
    status: str

    total: int
    success: int
    failed: int
    skipped: int

    created_at: datetime
    updated_at: datetime
