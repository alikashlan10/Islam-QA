import uuid

from src.domain.models.transcript import Transcript
from src.infrastructure.persistence.orm_models import TranscriptORM


class TranscriptMapper:

    @staticmethod
    def to_orm(transcript: Transcript, video_id: str) -> TranscriptORM:
        return TranscriptORM(
            id        = str(uuid.uuid4()),
            video_id  = video_id,
            full_text = transcript.full_text,
            language  = transcript.language,
        )
