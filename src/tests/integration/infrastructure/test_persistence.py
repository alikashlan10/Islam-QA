"""
Integration Tests for Persistence Layer
=========================================
(Updated: QA extraction removed, embedding moved to Transcript)
"""

import uuid
import pytest
from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.config import AppConfig
from src.infrastructure.persistence.orm_models import (
    Base, PlaylistORM, AudioMetadataORM, TranscriptORM
)
from src.infrastructure.persistence.repositories.playlist_repository import PlaylistRepository
from src.infrastructure.persistence.repositories.audio_metadata_repository import AudioMetadataRepository
from src.infrastructure.persistence.repositories.transcript_repository import TranscriptRepository

config = AppConfig()


# ── Test Database Setup ───────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def test_engine():
    engine = create_engine(config.TEST_DATABASE_URL)
    yield engine
    engine.dispose()


@pytest.fixture(autouse=True)
def setup_tables(test_engine):
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def override_db_engine(test_engine, monkeypatch):
    import src.infrastructure.persistence.database as db_module

    monkeypatch.setattr(db_module, "engine", test_engine)

    TestSessionLocal = sessionmaker(
        bind=test_engine,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False
    )
    monkeypatch.setattr(db_module, "SessionLocal", TestSessionLocal)


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_playlist(id: str = "PLxxxxxxxxxxxxxxxx") -> PlaylistORM:
    return PlaylistORM(
        id=id,
        title="شرح الميراث",
        channel_name="قناة العلم",
        channel_url="https://youtube.com/@testchannel",
    )


def make_audio(video_id: str = "dQw4w9WgXcQ", playlist_id: str = None) -> AudioMetadataORM:
    return AudioMetadataORM(
        id=video_id,
        title="Test Video",
        file_name=f"{video_id}.mp3",
        file_path=f"/tmp/audio/{video_id}.mp3",
        playlist_id=playlist_id,
        channel_name="Test Channel",
        channel_url="https://youtube.com/@test",
        duration_seconds=120.0,
        upload_date=datetime(2024, 1, 1, tzinfo=timezone.utc),
        description="Test description",
        thumbnail_url="https://img.youtube.com/test.jpg",
        language="ar",
        tags="فقه,ميراث",
        downloaded_at=datetime.now(timezone.utc),
        transcribed=False,
        # ❌ qa_extracted removed
        # ❌ embedded removed
    )


def make_transcript(video_id: str = "dQw4w9WgXcQ") -> TranscriptORM:
    return TranscriptORM(
        id=str(uuid.uuid4()),
        video_id=video_id,
        full_text="والأعمام يسقطون...",
        language="ar",
        created_at=datetime.now(timezone.utc),
        embedded=False  # ✅ now exists here
    )


# ── Playlist Repository Tests ─────────────────────────────────────────────────

@pytest.mark.integration
class TestPlaylistRepository:

    def test_save_and_get_by_id(self, override_db_engine):
        repo = PlaylistRepository()
        playlist = make_playlist()

        repo.save(playlist)
        result = repo.get_by_id("PLxxxxxxxxxxxxxxxx")

        assert result is not None
        assert result.id == "PLxxxxxxxxxxxxxxxx"
        assert result.title == "شرح الميراث"

    def test_exists(self, override_db_engine):
        repo = PlaylistRepository()
        repo.save(make_playlist())

        assert repo.exists("PLxxxxxxxxxxxxxxxx") is True
        assert repo.exists("nonexistent") is False


# ── AudioMetadata Repository Tests ────────────────────────────────────────────

@pytest.mark.integration
class TestAudioMetadataRepository:

    def test_save_and_get_by_id(self, override_db_engine):
        repo = AudioMetadataRepository()
        repo.save(make_audio())

        result = repo.get_by_id("dQw4w9WgXcQ")

        assert result is not None
        assert result.id == "dQw4w9WgXcQ"

    def test_get_unprocessed(self, override_db_engine):
        repo = AudioMetadataRepository()

        a1 = make_audio("v1")
        a2 = make_audio("v2")
        a2.transcribed = True

        repo.save(a1)
        repo.save(a2)

        results = repo.get_unprocessed()

        assert len(results) == 1
        assert results[0].id == "v1"

    def test_update_flags(self, override_db_engine):
        repo = AudioMetadataRepository()
        repo.save(make_audio())

        repo.update_flags("dQw4w9WgXcQ", transcribed=True)

        result = repo.get_by_id("dQw4w9WgXcQ")
        assert result.transcribed is True


# ── Transcript Repository Tests ───────────────────────────────────────────────

@pytest.mark.integration
class TestTranscriptRepository:

    def test_save_and_get(self, override_db_engine):
        audio_repo = AudioMetadataRepository()
        transcript_repo = TranscriptRepository()

        audio_repo.save(make_audio())
        transcript_repo.save(make_transcript())

        result = transcript_repo.get_by_video_id("dQw4w9WgXcQ")

        assert result is not None
        assert result.full_text == "والأعمام يسقطون..."
        assert result.embedded is False

    def test_mark_as_embedded(self, override_db_engine):
        audio_repo = AudioMetadataRepository()
        transcript_repo = TranscriptRepository()

        audio_repo.save(make_audio())
        transcript_repo.save(make_transcript())

        transcript_repo.mark_as_embedded("dQw4w9WgXcQ")

        result = transcript_repo.get_by_video_id("dQw4w9WgXcQ")
        assert result.embedded is True

    def test_is_embedded(self, override_db_engine):
        audio_repo = AudioMetadataRepository()
        transcript_repo = TranscriptRepository()

        audio_repo.save(make_audio())
        transcript_repo.save(make_transcript())

        assert transcript_repo.is_embedded("dQw4w9WgXcQ") is False

        transcript_repo.mark_as_embedded("dQw4w9WgXcQ")

        assert transcript_repo.is_embedded("dQw4w9WgXcQ") is True