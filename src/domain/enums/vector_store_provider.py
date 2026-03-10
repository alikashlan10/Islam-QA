from enum import Enum

class VectorStoreProvider(str, Enum):
    QDRANT   = "qdrant"
    CHROMA   = "chroma"
    PINECONE = "pinecone"
