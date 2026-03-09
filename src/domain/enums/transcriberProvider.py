from enum import Enum

class TranscriberProvider(str, Enum):
    WHISPER_LOCAL = "whisper"
    GROQ          = "groq"
    ASSEMBLY      = "assemblyai"