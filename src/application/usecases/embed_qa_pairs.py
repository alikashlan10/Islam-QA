"""
EmbedQAPairs Use Case
======================
Embeds all unembedded QA pairs into the vector store.
Supports force re-embedding for model upgrades — call execute(force=True)
after bumping QDRANT_COLLECTION_NAME in .env.
"""

from typing import List
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStore
from langchain_text_splitters import TextSplitter

from src.infrastructure.persistence.repositories.qa_pair_repository import QAPairRepository
from src.infrastructure.persistence.repositories.audio_metadata_repository import AudioMetadataRepository
from src.logger.logger import setup_logger

logger = setup_logger(__name__)


class EmbedQAPairsUseCase:

    def __init__(
        self,
        chunker:      TextSplitter,
        vector_store: VectorStore,
        qa_repo:      QAPairRepository,
    ) -> None:
        self._chunker      = chunker
        self._vector_store = vector_store
        self._qa_repo      = qa_repo

    def execute(self, force: bool = False) -> None:

        # ── Step 1: Get QA pairs to embed ─────────────────────────────────────

        if force:
            logger.info("Force re-embedding — resetting all embedding IDs")
            self._qa_repo.reset_embedding_ids()
            qa_pairs = self._qa_repo.get_all()
        else:
            qa_pairs = self._qa_repo.get_unembedded()

        if not qa_pairs:
            logger.info("No QA pairs to embed.")
            return

        logger.info(f"Embedding {len(qa_pairs)} QA pairs...")

        # ── Step 2: Embed each QA pair ────────────────────────────────────────

        success = 0
        failed  = 0

        for qa in qa_pairs:
            try:
                # build text — answer-first for better semantic representation
                text = f"سؤال: {qa.question}\nجواب: {qa.answer}"

                # chunk
                chunks = self._chunker.split_text(text)

                if not chunks:
                    logger.warning(f"No chunks generated for QA pair: {qa.id}")
                    continue

                # build documents
                docs = [
                    Document(
                        page_content=chunk,
                        metadata={
                            "qa_pair_id":  qa.id,
                            "question":    qa.question,
                            "answer":      qa.answer,
                            "video_id":    qa.video_id,
                            "chunk_index": i,
                        }
                    )
                    for i, chunk in enumerate(chunks)
                ]

                # generate chunk ids
                ids = [f"{qa.id}_chunk_{i}" for i in range(len(chunks))]

                # embed + store — LangChain handles embedding internally
                self._vector_store.add_documents(documents=docs, ids=ids)

                # update DB — store first chunk id as reference
                self._qa_repo.update_embedding_id(qa.id, ids[0])

                success += 1

            except Exception as e:
                logger.error(f"Failed to embed QA pair {qa.id}: {e}")
                failed += 1
                continue

        logger.info(f"Embedding complete — {success} succeeded, {failed} failed")
