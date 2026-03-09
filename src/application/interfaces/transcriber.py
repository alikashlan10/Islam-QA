from abc import ABC , abstractmethod
from src.domain.models.transcript import Transcript


class Transcriber(ABC):
    """Interface defines the behavior of the Transcriper"""
    @abstractmethod
    def transcribe(self, audio_path: str) -> Transcript:
        pass