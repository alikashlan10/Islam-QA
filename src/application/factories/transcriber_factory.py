from src.application.interfaces.transcriber import Transcriber
from src.domain.enums.transcriberProvider import TranscriberProvider

class TranscriberFactory:
    def create(self, provider: TranscriberProvider) -> Transcriber:
        if provider == TranscriberProvider.WHISPER_LOCAL:

            from src.infrastructure.transcribers.whisperLocalTranscriber import WhisperLocalTranscriber
            return WhisperLocalTranscriber()
        
        elif provider == TranscriberProvider.GROQ:

            from src.infrastructure.transcribers.groqTranscriber import GroqTranscriber
            return GroqTranscriber()
        
        else:
            raise ValueError(f"Unsupported transcriber provider: {provider}")