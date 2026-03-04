from abc import ABC, abstractmethod
from typing import List
from src.domain.models.qaPair import QAPair

class QAExtractor(ABC):
    @abstractmethod
    def extract(self, text: str) -> List[QAPair]:
        """
        Extract QA pairs from a block of text.
        Returns a list of QAPair instances. (In case there are multiple questions)
        """
        pass