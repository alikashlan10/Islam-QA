from langchain_text_splitters import (
    TextSplitter,
    RecursiveCharacterTextSplitter,
    TokenTextSplitter,
    NLTKTextSplitter,
)
from src.domain.enums.chunking_strategy import ChunkingStrategy
from typing import List


from src.logger.logger import setup_logger
logger = setup_logger(__name__)


class ChunkerFactory:
    """
    Creates LangChain TextSplitter instances.
    All providers implement the same TextSplitter base class.
    """

    def create(
        self,
        strategy:      ChunkingStrategy,
        chunk_size:    int,
        chunk_overlap: int,
        separators:    list, 
    ) -> TextSplitter:

        logger.info(f"Creating chunker: strategy={strategy} "
                    f"chunk_size={chunk_size} chunk_overlap={chunk_overlap}")

        if strategy == ChunkingStrategy.RECURSIVE:
            return RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                separators=separators,
            )

        elif strategy == ChunkingStrategy.TOKEN:
            return TokenTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            )

        elif strategy == ChunkingStrategy.SENTENCE:
            # NLTKTextSplitter ignores chunk_size — splits on sentence boundaries
            return NLTKTextSplitter()

        else:
            raise ValueError(f"Unsupported chunker provider: {strategy}")
