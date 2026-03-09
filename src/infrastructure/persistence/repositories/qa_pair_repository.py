from typing import List, Optional

from src.infrastructure.persistence.orm_models import QAPairORM
from src.infrastructure.persistence.database import get_db
from src.logger.logger import setup_logger

logger = setup_logger(__name__)


class QAPairRepository:

    def save_batch(self, qa_pairs: List[QAPairORM]) -> None:
        """
        Insert multiple QA pairs at once.
        Used after LLM extraction — always returns a list, never a single pair.
        """
        with get_db() as db:
            db.add_all(qa_pairs)
            logger.info(f"Saved {len(qa_pairs)} QA pairs.")

    def get_by_video_id(self, video_id: str) -> List[QAPairORM]:
        """Fetch all QA pairs extracted from a specific video."""
        with get_db() as db:
            return (
                db.query(QAPairORM)
                .filter(QAPairORM.video_id == video_id)
                .all()
            )

    def get_unembedded(self) -> List[QAPairORM]:
        """
        Fetch all QA pairs that haven't been embedded yet.
        Used to resume embedding step without reprocessing already embedded pairs.
        """
        with get_db() as db:
            return (
                db.query(QAPairORM)
                .filter(QAPairORM.embedding_id == None)
                .all()
            )

    def update_embedding_id(self, qa_pair_id: str, embedding_id: str) -> None:
        """
        Store the vector DB reference after a QA pair has been embedded.
        Links the relational DB record to its vector DB counterpart.
        """
        with get_db() as db:
            qa_pair = db.get(QAPairORM, qa_pair_id)
            if not qa_pair:
                logger.warning(f"QA pair not found: {qa_pair_id}")
                return

            qa_pair.embedding_id = embedding_id
            logger.info(f"Updated embedding_id for QA pair: {qa_pair_id}")