from pydantic_settings import BaseSettings
from src.domain.enums.transcriberProvider import TranscriberProvider
import os 

class AppConfig(BaseSettings):

    # Logs
    LOG_LEVEL:str
    LOG_FILE:str

    # LLMs
    GEMINI_API_KEY:str
    GEMINI_MODEL_NAME:str

    ## transcriber provider
    TRANSCRIBER_PROVIDER:TranscriberProvider = TranscriberProvider.WHISPER_LOCAL
    GROQ_API_KEY:str
    GROQ_WHISPER_MDOEL:str
    
    class Config:
        env_file = ".env"

