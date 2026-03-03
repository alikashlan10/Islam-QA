from pydantic_settings import BaseSettings


class AppConfig(BaseSettings):

    # Logs
    LOG_LEVEL:str
    LOG_FILE:str

    

    class Config:
        env_file = ".env"

