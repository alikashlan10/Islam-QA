from pydantic_settings import BaseSettings


class AppConfig(BaseSettings):

    # Logs
    LOG_LEVEL:str
    LOG_FILE:str

    # LLMs
    GEMINI_API_KEY:str
    GEMINI_MODEL_NAME:str

    class Config:
        env_file = ".env"

