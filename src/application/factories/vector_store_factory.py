from langchain_core.vectorstores import VectorStore
from src.domain.enums.vector_store_provider import VectorStoreProvider
from langchain_core.embeddings import Embeddings
from langchain_qdrant import QdrantVectorStore
from langchain_community.vectorstores import Chroma


from src.logger.logger import setup_logger
logger = setup_logger(__name__)

class VectorStoreFactory:
    """
    Creates LangChain VectorStore instances.
    All providers implement the same VectorStore base class.
    Embedder is passed in — vector store uses it internally for query embedding.
    """

    def create(
        self,
        provider:        VectorStoreProvider,
        embedder:        Embeddings,
        collection_name: str,
        # Qdrant
        qdrant_url:      str = None,
        # Chroma
        chroma_persist_dir: str = None,
    ) -> VectorStore:

        logger.info(f"Creating vector store: provider={provider} collection={collection_name}")

        if provider == VectorStoreProvider.QDRANT:
            return QdrantVectorStore.from_existing_collection(
                embedding=embedder,
                collection_name=collection_name,
                url=qdrant_url,
            )

        elif provider == VectorStoreProvider.CHROMA:
            return Chroma(
                embedding_function=embedder,
                collection_name=collection_name,
                persist_directory=chroma_persist_dir,
            )

     

        else:
            raise ValueError(f"Unsupported vector store provider: {provider}")