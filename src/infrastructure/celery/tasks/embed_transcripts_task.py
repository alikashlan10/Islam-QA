from src.infrastructure.celery.celery_app import celery_app
from src.application.usecases.embed_transcribts import EmbedTranscriptUseCase
from src.application.factories.chunking_factory import ChunkerFactory
from src.application.factories.embedder_factory import EmbedderFactory
from src.application.factories.vector_store_factory import VectorStoreFactory
from src.infrastructure.persistence.repositories.transcript_repository import TranscriptRepository
from src.infrastructure.persistence.repositories.audio_metadata_repository import AudioMetadataRepository
from src.infrastructure.persistence.repositories.job_repository import JobRepository
from src.infrastructure.persistence.orm_models import JobORM 
from src.domain.enums.separators import Separators
from src.config import AppConfig
from src.logger.logger import setup_logger

@celery_app.task(name="embed_transcripts_task")
def embed_transcript_task(batch_size , job_id , force):

    # define dependencies
    config=AppConfig()
    logger=setup_logger(__name__)
    job_repo = JobRepository()

    
    try :

        # mark as running
        job_repo.set_status(job_id, "running")
        logger.info(f"job {job_id} is running")

        chunker = ChunkerFactory().create(
        strategy      = config.CHUNKING_STRATEGY,
        chunk_size    = config.CHUNK_SIZE,
        chunk_overlap = config.CHUNK_OVERLAP,
        separators    = Separators.ARABIC,
        )
        
        embedder = EmbedderFactory().create(
            provider=config.EMBEDDING_PROVIDER ,
            model_name= config.EMBEDDING_MODEL_NAME ,
            api_key= config.COHERE_API_KEY
        )

        vector_store = VectorStoreFactory().create(
            provider        = config.VECTOR_STORE_PROVIDER,
            embedder        = embedder,
            collection_name = config.QDRANT_COLLECTION_NAME,
            qdrant_url      = config.QDRANT_URL,
            qdrant_api_key  = config.QDRANT_API_KEY
        )

        # define use case
        use_case = EmbedTranscriptUseCase(
            chunker= chunker, 
            vector_store=vector_store,
            transcript_repo= TranscriptRepository() , 
            audio_repo = AudioMetadataRepository(),
            job_repo= job_repo , 
            batch_size = batch_size
        )
        # execute use case
        use_case.execute(job_id=job_id , force=force)

        job_repo.update(job_id=job_id , status = "success")


    except Exception as e :

        logger.info(f"Task failed : {e}")
        job_repo.update(job_id=job_id , status = "failed")