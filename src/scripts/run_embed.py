from src.api.dependencies import embed_transcripts_use_case
from src.logger.logger import setup_logger

logger = setup_logger(__name__)

if __name__ == "__main__":

    logger.info("")
    logger.info("="*30)
    logger.info("="*30)
    logger.info("Starting Embed process")
    logger.info("="*30)
    logger.info("="*30)
    logger.info("")

    embed_transcripts_use_case.execute(force=False)

    
