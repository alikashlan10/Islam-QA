from src.application.interfaces.transcriber import Transcriber
from src.domain.models.transcript import Transcript

class WhisperLocalTranscriber(Transcriber):
    
    def transcribe(self, audio_path: str) -> Transcript:
        pass