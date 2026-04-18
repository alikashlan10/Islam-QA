from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from typing import Generator

from src.infrastructure.persistence.orm_models import Base
from src.logger.logger import setup_logger
from src.config import AppConfig

logger = setup_logger(__name__)
config = AppConfig()


engine = create_engine(
    config.TEST_DATABASE_URL,
    echo=False,          # set to True to log all SQL statements (useful for debugging)
    pool_pre_ping=True,  # test connections before using them — handles dropped connections
)


SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


@contextmanager
def get_db() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()   # undo any changes if something went wrong
        raise
    finally:
        session.close()      # always release the connection back to the pool


def init_db() -> None:
    logger.info("Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables ready.")