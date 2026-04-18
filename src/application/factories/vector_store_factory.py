from langchain_core.vectorstores import VectorStore
from src.domain.enums.vector_store_provider import VectorStoreProvider
from langchain_core.embeddings import Embeddings
from langchain_qdrant import QdrantVectorStore
from langchain_community.vectorstores import Chroma
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from src.config import AppConfig

from src.logger.logger import setup_logger
logger = setup_logger(__name__)

config = AppConfig()

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
        qdrant_api_key: str =None,
        # Chroma
        chroma_persist_dir: str = None,
    ) -> VectorStore:

        logger.info(f"Creating vector store: provider={provider} collection={collection_name}")

        if provider == VectorStoreProvider.QDRANT:

            client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
    
            # create collection if it doesn't exist
            existing = [c.name for c in client.get_collections().collections]
            if collection_name not in existing:
                client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=config.QDRANT_VECTOR_SIZE,
                        distance=Distance.COSINE,
                    ),
                )

            return QdrantVectorStore(
                client=client,
                collection_name=collection_name,
                embedding=embedder,
            )

        elif provider == VectorStoreProvider.CHROMA:
            return Chroma(
                embedding_function=embedder,
                collection_name=collection_name,
                persist_directory=chroma_persist_dir,
            )

     

        else:
            raise ValueError(f"Unsupported vector store provider: {provider}")