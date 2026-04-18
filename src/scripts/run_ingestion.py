"""
Test Ingestion Script
======================
Runs the full ingestion pipeline for a single video from a playlist.
Use this to verify the pipeline works end to end before the API layer.

Usage:
    python scripts/test_ingestion.py
"""

from src.infrastructure.persistence.database import init_db
from src.api.dependencies import ingest_playlist_use_case
from src.logger.logger import setup_logger

logger = setup_logger(__name__)


PLAYLIST_URL = "https://www.youtube.com/playlist?list=PL6C71skKjoGsHYPmniKWbQV7jKMFjYVdz"
LIMIT        = 1   # process only one video

# ── Run ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":

    logger.info("")
    logger.info("="*30)
    logger.info("="*30)
    logger.info("Starting Ingestion process")
    logger.info("="*30)
    logger.info("="*30)
    logger.info("")

    logger.info("Initializing database...")
    init_db()

    # Step 1 — ingest one video from playlist
    logger.info(f"Starting ingestion: {PLAYLIST_URL} (limit={LIMIT})")
    result = ingest_playlist_use_case.execute(
        playlist_url = PLAYLIST_URL,
        limit        = LIMIT,
    )

    logger.info(f"Ingestion result:")
    logger.info(f"  playlist_id : {result.playlist_id}")
    logger.info(f"  total       : {result.total}")
    logger.info(f"  success     : {result.success}")
    logger.info(f"  skipped     : {result.skipped}")
    logger.info(f"  failed      : {result.failed}")

    if result.success == 0:
        logger.error("No videos were successfully ingested. Check logs above.")
        exit(1)

    # # Step 2 — embed extracted QA pairs
    # logger.info("Starting embedding...")
    # embed_qa_pairs_use_case.execute()

    #logger.info("Pipeline complete. Check your Qdrant dashboard at http://localhost:6333/dashboard")