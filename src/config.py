from pydantic_settings import BaseSettings
from src.domain.enums.transcriberProvider import TranscriberProvider
from src.domain.enums.chunking_strategy import ChunkingStrategy
from src.domain.enums.vector_store_provider import VectorStoreProvider
from src.domain.enums.embedder_provider import EmbedderProvider
import os 

class AppConfig(BaseSettings):

    # Logs
    LOG_LEVEL:str = "INFO"
    LOG_FILE:str = "logs/app.log"


    # LLMs
    GEMINI_API_KEY:str = ""
    GEMINI_MODEL_NAME:str = "gemini-1.5-flash"
    GROQ_LLM_MODEL:str = "openai/gpt-oss-120b"

    ## transcriber provider
    TRANSCRIBER_PROVIDER:TranscriberProvider = TranscriberProvider.GROQ
    GROQ_API_KEY:str = ""
    GROQ_WHISPER_MODEL:str = "whisper-large-v3"
    
    ##database
    DATABASE_URL:str = ""
    TEST_DATABASE_URL:str = ""

    ##Vectordb
    QDRANT_URL:str = ""
    QDRANT_COLLECTION_NAME:str = "islam_qa_v1"
    QDRANT_VECTOR_SIZE : int = 512
    
    ##Emebdding model
    EMBEDDING_MODEL_NAME:str = ""

    ##app
    VECTOR_STORE_PROVIDER:  VectorStoreProvider= VectorStoreProvider.QDRANT
    EMBEDDING_PROVIDER:     EmbedderProvider   = EmbedderProvider.HUGGINGFACE
    CHUNKING_STRATEGY:      ChunkingStrategy   = ChunkingStrategy.RECURSIVE
    CHUNK_SIZE:             int                = 500
    CHUNK_OVERLAP:          int                = 100
    AUDIO_OUTPUT_DIR:       str                = "./video_downloads"

    class Config:
        env_file = ".env"

