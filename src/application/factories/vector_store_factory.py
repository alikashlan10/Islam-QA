from langchain_core.vectorstores import VectorStore
from langchain_core.embeddings import Embeddings
from langchain_qdrant import QdrantVectorStore, FastEmbedSparse, RetrievalMode
from langchain_community.vectorstores import Chroma
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    SparseVectorParams,
    SparseIndexParams,
)

from src.domain.enums.vector_store_provider import VectorStoreProvider
from src.config import AppConfig
from src.logger.logger import setup_logger

logger = setup_logger(__name__)
config = AppConfig()


class VectorStoreFactory:
    """
    Creates LangChain VectorStore instances.
    Qdrant supports hybrid search (dense + sparse/BM25).
    Embedder is passed in — vector store uses it internally for query embedding.
    """

    def create(
        self,
        provider:           VectorStoreProvider,
        embedder:           Embeddings,
        collection_name:    str,
        # Qdrant
        qdrant_url:         str = None,
        qdrant_api_key:     str = None,
        # Chroma
        chroma_persist_dir: str = None,
    ) -> VectorStore:

        logger.info(f"Creating vector store: provider={provider} collection={collection_name}")

        if provider == VectorStoreProvider.QDRANT:
            return self._create_qdrant(
                embedder        = embedder,
                collection_name = collection_name,
                qdrant_url      = qdrant_url,
                qdrant_api_key  = qdrant_api_key,
            )

        elif provider == VectorStoreProvider.CHROMA:
            return Chroma(
                embedding_function=embedder,
                collection_name=collection_name,
                persist_directory=chroma_persist_dir,
            )

        else:
            raise ValueError(f"Unsupported vector store provider: {provider}")

    def _create_qdrant(
        self,
        embedder:        Embeddings,
        collection_name: str,
        qdrant_url:      str,
        qdrant_api_key:  str,
    ) -> QdrantVectorStore:

        client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)

        # create collection with both dense + sparse vectors if not exists
        existing = [c.name for c in client.get_collections().collections]
        if collection_name not in existing:
            logger.info(f"Creating hybrid collection: {collection_name}")
            client.create_collection(
                collection_name=collection_name,
                vectors_config={
                    "dense": VectorParams(
                        size=config.QDRANT_VECTOR_SIZE,
                        distance=Distance.COSINE,
                    ),
                },
                sparse_vectors_config={
                    "sparse": SparseVectorParams(
                        index=SparseIndexParams(on_disk=False),
                    )
                },
            )
        else:
            logger.info(f"Collection already exists: {collection_name}")

        # sparse embedder — BM25 style, language agnostic
        sparse_embedder = FastEmbedSparse(model_name="Qdrant/bm25")

        return QdrantVectorStore(
            client             = client,
            collection_name    = collection_name,
            embedding          = embedder,          # dense vectors
            sparse_embedding   = sparse_embedder,   # sparse vectors (BM25)
            retrieval_mode     = RetrievalMode.HYBRID,
            vector_name        = "dense",
            sparse_vector_name = "sparse",
        )