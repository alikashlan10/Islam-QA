from enum import Enum

class EmbedderProvider(Enum):
    
    HUGGINGFACE = "huggingface"
    OPENAI      = "openai"
    COHERE      = "cohere"
    GOOGLE      = "google"