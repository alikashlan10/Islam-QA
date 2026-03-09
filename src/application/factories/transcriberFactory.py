from src.application.interfaces.transcriber import Transcriber
from src.domain.enums.transcriberProvider import TranscriberProvider
from src.infrastructure.transcribers.whisperLocalTranscriber import WhisperLocalTranscriber
from src.infrastructure.transcribers.groqTranscriber import GroqTranscriber

class TranscriberFactory:
    def create(self, provider: TranscriberProvider) -> Transcriber:
        if provider == TranscriberProvider.WHISPER_LOCAL:
            return WhisperLocalTranscriber()
        elif provider == TranscriberProvider.GROQ:
            return GroqTranscriber()
        else:
            raise ValueError(f"Unsupported transcriber provider: {provider}")