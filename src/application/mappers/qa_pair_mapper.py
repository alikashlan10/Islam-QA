import uuid

from src.domain.models.qa_pair import QAPair
from src.infrastructure.persistence.orm_models import QAPairORM


class QAPairMapper:

    @staticmethod
    def to_orm(
        qa_pair:       QAPair,
        video_id:      str,
        transcript_id: str,
    ) -> QAPairORM:
        return QAPairORM(
            id            = str(uuid.uuid4()),
            video_id      = video_id,
            transcript_id = transcript_id,
            question      = qa_pair.question,
            answer        = qa_pair.answer,
            embedding_id  = None,
        )
