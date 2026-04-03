from src.application.interfaces.qa_extractor import QAExtractor
from src.domain.enums.qa_extractor_provider import QAExtractorProvider

class QAExtractorFactory:
    def create(self, provider: QAExtractorProvider) -> QAExtractor:
        if provider == QAExtractorProvider.GEMINI:

            from src.infrastructure.extractors.geminiQAExtractor import GeminiQAExtractor
            return GeminiQAExtractor()
        
        else:
            raise ValueError(f"Unsupported qa extractor provider: {provider}")