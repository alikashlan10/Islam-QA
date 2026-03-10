from pydantic_settings import BaseSettings
from src.domain.enums.transcriberProvider import TranscriberProvider
import os 

class AppConfig(BaseSettings):

    # Logs
    LOG_LEVEL:str = "INFO"
    LOG_FILE:str = "logs/app.log"


    # LLMs
    GEMINI_API_KEY:str = ""
    GEMINI_MODEL_NAME:str = "gemini-1.5-flash"

    ## transcriber provider
    TRANSCRIBER_PROVIDER:TranscriberProvider = TranscriberProvider.GROQ
    GROQ_API_KEY:str = ""
    GROQ_WHISPER_MODEL:str = "whisper-large-v3"
    
    ##database
    DATABASE_URL:str = ""
    TEST_DATABASE_URL:str = ""

    class Config:
        env_file = ".env"

