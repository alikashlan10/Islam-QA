from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStore
from langchain_text_splitters import TextSplitter

from src.infrastructure.persistence.repositories.transcript_repository import TranscriptRepository
from src.infrastructure.persistence.repositories.audio_metadata_repository import AudioMetadataRepository
from src.infrastructure.persistence.orm_models import TranscriptORM
from src.infrastructure.persistence.repositories.job_repository import JobRepository
from src.logger.logger import setup_logger
from src.config import AppConfig
import uuid

logger = setup_logger(__name__)
config = AppConfig()

class EmbedTranscriptUseCase:

    def __init__(
        self,
        chunker: TextSplitter,
        vector_store: VectorStore,
        transcript_repo: TranscriptRepository,
        audio_repo: AudioMetadataRepository,
        job_repo : JobRepository, 
        batch_size: int = 100,
    ) -> None:
        self._chunker = chunker
        self._vector_store = vector_store
        self._transcript_repo = transcript_repo
        self._audio_repo = audio_repo
        self._batch_size = batch_size
        self._job_repo = job_repo

    def execute(self, job_id , force: bool = False) -> None:

        logger.info(f"Starting embedding process | force={force}")

        success = 0
        failed = 0
        total = 0

        # ─────────────────────────────────────────────────────────────
        # NORMAL MODE (ONLY UNEMBEDDED)
        # ─────────────────────────────────────────────────────────────
        if not force:

            # get total
            total += self._transcript_repo.count_unembedded()
            logger.info(F"Total unembedded transcripts : {total}")
            self._job_repo.update(job_id=job_id , total = total)


            while True:

                transcripts = self._transcript_repo.get_unembedded(limit=self._batch_size)
                logger.info(f"loaded {len(transcripts)} from database")

                if not transcripts:
                    logger.info("No more unembedded transcripts.")
                    break
                


                try:
                    docs, ids, video_ids  = self._prepare_batch(transcripts, job_id)

                    if not docs:
                        continue
                    
                    logger.info("Adding documents to vector store")
                    self._vector_store.add_documents(documents=docs, ids=ids)
                    logger.info(f"Added {len(docs)} to {config.VECTOR_STORE_PROVIDER.value}")

                    # mark as embedded AFTER success
                    for vid in video_ids:
                        self._transcript_repo.mark_as_embedded(vid)

                    success += len(video_ids)
                    self._job_repo.increment_success(job_id=job_id , count = len(video_ids) )
                    

                except Exception as e:
                    logger.error(f"Batch embedding failed: {e}")
                    failed += len(transcripts)
                    self._job_repo.increment_failed(job_id=job_id ,count = len(transcripts))
                    break

        # ─────────────────────────────────────────────────────────────
        # FORCE MODE (RE-EMBED EVERYTHING)
        # ─────────────────────────────────────────────────────────────
        else:

            offset = 0
            total += self._transcript_repo.count_all()
            logger.info(F"Total transcripts : {total}")
            self._job_repo.update(job_id=job_id , total = total)


            while True:
                transcripts = self._transcript_repo.get_all(
                    limit=self._batch_size,
                    offset=offset
                )

                if not transcripts:
                    logger.info("Finished re-embedding all transcripts.")
                    break


                try:
                    docs, ids, video_ids  = self._prepare_batch(transcripts , job_id)

                    if not docs:
                        continue

                    logger.info("Adding documents to vector store")
                    self._vector_store.add_documents(documents=docs, ids=ids)
                    logger.info(f"Added {len(docs)} to {config.VECTOR_STORE_PROVIDER.value}")

                    success += len(transcripts)
                    self._job_repo.increment_success(job_id=job_id , count = len(video_ids) )

                except Exception as e:
                    logger.error(f"Batch embedding failed: {e}")
                    failed += len(transcripts , count=len(transcripts))
                    self._job_repo.increment_failed(job_id=job_id , count = len(transcripts))

                offset += self._batch_size

        logger.info(f"Embedding complete — total : {total} ,  {success} succeeded, {failed} failed")

    # ─────────────────────────────────────────────────────────────
    # INTERNAL: PREPARE BATCH
    # ─────────────────────────────────────────────────────────────
    def _prepare_batch(self, transcripts : list[TranscriptORM], job_id):

        logger.info("preparing batch")

        docs = []
        ids = []
        video_ids = []

        for transcript in transcripts:

            audio = self._audio_repo.get_by_id(transcript.video_id)

            logger.info("splitting text")
            chunks = self._chunker.split_text(transcript.full_text)

            if not chunks:
                logger.warning(f"No chunks for transcript: {transcript.video_id}")
                self._job_repo.increment_skipped(job_id=job_id)
                continue

            logger.info("appending Documents")    
            for i, chunk in enumerate(chunks):
                docs.append(
                    Document(
                        page_content=chunk,
                        metadata={
                            "video_id": transcript.video_id,
                            "chunk_index": i,
                            "thumbnail_url": audio.thumbnail_url if audio else None,
                            "title": audio.title if audio else None,
                        }
                    )
                )

                ids.append(uuid.uuid4())

            video_ids.append(transcript.video_id)

        return docs, ids, video_ids 