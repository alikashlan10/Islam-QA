"""
Dependencies
=============
Composition root — creates and wires all concrete implementations.
All objects are module-level singletons, created once at startup.

Import directly in endpoints:
    from src.api.dependencies import ingest_playlist_use_case
"""

from src.config import AppConfig
from src.logger.logger import setup_logger

# ── Factories ─────────────────────────────────────────────────────────────────
from src.application.factories.transcriber_factory import TranscriberFactory
from src.application.factories.chunking_factory import ChunkerFactory
from src.application.factories.embedder_factory import EmbedderFactory
from src.application.factories.vector_store_factory import VectorStoreFactory

# ── Infrastructure ────────────────────────────────────────────────────────────
from src.infrastructure.youtube.yt_dlp_playlist_fetcher import YtDlpPlaylistFetcher
from src.infrastructure.youtube.yt_dlp_audio_downloader import YtDlpAudioDownloader
from src.infrastructure.persistence.repositories.playlist_repository import PlaylistRepository
from src.infrastructure.persistence.repositories.audio_metadata_repository import AudioMetadataRepository
from src.infrastructure.persistence.repositories.transcript_repository import TranscriptRepository
from src.domain.enums.separators import Separators

# ── Use Cases ─────────────────────────────────────────────────────────────────
from src.application.usecases.ingest_video import IngestVideoUseCase
from src.application.usecases.ingest_playlist import IngestPlaylistUseCase
from src.application.usecases.embed_transcribts import EmbedTranscriptUseCase

logger = setup_logger(__name__)
config = AppConfig()

# ── Transcriber ───────────────────────────────────────────────────────────────

transcriber = TranscriberFactory().create(
    provider = config.TRANSCRIBER_PROVIDER,
)


# ── Downloader + Fetcher ──────────────────────────────────────────────────────

downloader = YtDlpAudioDownloader()
fetcher    = YtDlpPlaylistFetcher()

# ── Repositories ──────────────────────────────────────────────────────────────

playlist_repo   = PlaylistRepository()
audio_repo      = AudioMetadataRepository()
transcript_repo = TranscriptRepository()

# ── Chunker ───────────────────────────────────────────────────────────────────

chunker = ChunkerFactory().create(
    strategy      = config.CHUNKING_STRATEGY,
    chunk_size    = config.CHUNK_SIZE,
    chunk_overlap = config.CHUNK_OVERLAP,
    separators    = Separators.ARABIC,
)

# ── Embedder ──────────────────────────────────────────────────────────────────

embedder = EmbedderFactory().create(
    provider   = config.EMBEDDING_PROVIDER,
    model_name = config.EMBEDDING_MODEL_NAME,
    api_key    = config.COHERE_API_KEY,   # only used if provider=google
)

# ── Vector Store ──────────────────────────────────────────────────────────────

vector_store = VectorStoreFactory().create(
    provider        = config.VECTOR_STORE_PROVIDER,
    embedder        = embedder,
    collection_name = config.QDRANT_COLLECTION_NAME,
    qdrant_url      = config.QDRANT_URL,
    qdrant_api_key  = config.QDRANT_API_KEY
)

# ── Use Cases ─────────────────────────────────────────────────────────────────

ingest_video_use_case = IngestVideoUseCase(
    downloader      = downloader,
    transcriber     = transcriber,
    audio_repo      = audio_repo,
    transcript_repo = transcript_repo,
)

ingest_playlist_use_case = IngestPlaylistUseCase(
    fetcher       = fetcher,
    playlist_repo = playlist_repo,
    ingest_video  = ingest_video_use_case,
)

embed_transcripts_use_case = EmbedTranscriptUseCase(
    chunker      = chunker,
    vector_store = vector_store,
    transcript_repo= transcript_repo ,
    audio_repo= audio_repo
)

logger.info("All dependencies initialized.")