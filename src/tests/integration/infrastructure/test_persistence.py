"""
Integration Tests for Persistence Layer
=========================================
Tests all repositories against a real PostgreSQL test database.

Setup:
    1. Create test DB: psql -U islam_qa -c "CREATE DATABASE islam_qa_test;"
    2. Add TEST_DATABASE_URL to .env
    3. Run: pytest src/tests/integration/persistence/ -v -m integration

These tests:
    - Use a real PostgreSQL database
    - Create all tables before each test
    - Drop all tables after each test (clean slate)
    - Never touch your development database
"""

import uuid
import pytest
from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.config import AppConfig
from src.infrastructure.persistence.orm_models import (
    Base, PlaylistORM, AudioMetadataORM, TranscriptORM, QAPairORM
)
from src.infrastructure.persistence.repositories.playlist_repository import PlaylistRepository
from src.infrastructure.persistence.repositories.audio_metadata_repository import AudioMetadataRepository
from src.infrastructure.persistence.repositories.transcript_repository import TranscriptRepository
from src.infrastructure.persistence.repositories.qa_pair_repository import QAPairRepository

config = AppConfig()


# ── Test Database Setup ───────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def test_engine():
    """
    Creates a SQLAlchemy engine connected to the TEST database.
    scope="session" means this runs once for the entire test session.
    """
    engine = create_engine(config.TEST_DATABASE_URL)
    yield engine
    engine.dispose()


@pytest.fixture(autouse=True)
def setup_tables(test_engine):
    """
    Creates all tables before each test, drops them after.
    autouse=True means this runs automatically for every test — no need to declare it.
    This guarantees each test starts with a clean empty database.
    """
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def override_db_engine(test_engine, monkeypatch):
    """
    Patches the engine in database.py to use the TEST engine instead of the real one.
    This ensures repositories use the test database without any code changes.
    monkeypatch automatically reverts changes after each test.
    """
    import src.infrastructure.persistence.database as db_module
    monkeypatch.setattr(db_module, "engine", test_engine)

    TestSessionLocal = sessionmaker(bind=test_engine, autocommit=False, autoflush=False ,expire_on_commit=False)
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
        qa_extracted=False,
        embedded=False,
    )


def make_transcript(video_id: str = "dQw4w9WgXcQ") -> TranscriptORM:
    return TranscriptORM(
        id=str(uuid.uuid4()),
        video_id=video_id,
        full_text="والأعمام يسقطون...",
        language="ar",
        created_at=datetime.now(timezone.utc),
    )


def make_qa_pair(video_id: str, transcript_id: str) -> QAPairORM:
    return QAPairORM(
        id=str(uuid.uuid4()),
        video_id=video_id,
        transcript_id=transcript_id,
        question="ما هو الميراث؟",
        answer="الميراث هو انتقال ملكية المتوفى إلى ورثته.",
        embedding_id=None,
        created_at=datetime.now(timezone.utc),
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
        assert result.id           == "PLxxxxxxxxxxxxxxxx"
        assert result.title        == "شرح الميراث"
        assert result.channel_name == "قناة العلم"

    def test_exists_returns_true_after_save(self, override_db_engine):
        repo = PlaylistRepository()
        repo.save(make_playlist())

        assert repo.exists("PLxxxxxxxxxxxxxxxx") is True

    def test_exists_returns_false_when_not_saved(self, override_db_engine):
        repo = PlaylistRepository()

        assert repo.exists("nonexistent_id") is False

    def test_save_updates_existing_playlist(self, override_db_engine):
        repo = PlaylistRepository()
        repo.save(make_playlist())

        # update the title
        updated = make_playlist()
        updated.title = "شرح الفرائض"
        repo.save(updated)

        result = repo.get_by_id("PLxxxxxxxxxxxxxxxx")
        assert result.title == "شرح الفرائض"

    def test_get_by_id_returns_none_when_not_found(self, override_db_engine):
        repo = PlaylistRepository()

        result = repo.get_by_id("nonexistent_id")
        assert result is None


# ── AudioMetadata Repository Tests ────────────────────────────────────────────

@pytest.mark.integration
class TestAudioMetadataRepository:

    def test_save_and_get_by_id(self, override_db_engine):
        repo = AudioMetadataRepository()
        repo.save(make_audio())

        result = repo.get_by_id("dQw4w9WgXcQ")

        assert result is not None
        assert result.id    == "dQw4w9WgXcQ"
        assert result.title == "Test Video"

    def test_get_by_playlist(self, override_db_engine):
        playlist_repo = PlaylistRepository()
        audio_repo    = AudioMetadataRepository()

        playlist_repo.save(make_playlist("PL123"))
        audio_repo.save(make_audio("video1", playlist_id="PL123"))
        audio_repo.save(make_audio("video2", playlist_id="PL123"))
        audio_repo.save(make_audio("video3", playlist_id=None))  # not in playlist

        results = audio_repo.get_by_playlist("PL123")

        assert len(results) == 2
        assert all(a.playlist_id == "PL123" for a in results)

    def test_get_unprocessed_returns_untranscribed(self, override_db_engine):
        repo = AudioMetadataRepository()

        audio1 = make_audio("video1")
        audio1.transcribed = False

        audio2 = make_audio("video2")
        audio2.transcribed = True   # already processed

        repo.save(audio1)
        repo.save(audio2)

        results = repo.get_unprocessed()

        assert len(results) == 1
        assert results[0].id == "video1"

    def test_update_flags(self, override_db_engine):
        repo = AudioMetadataRepository()
        repo.save(make_audio())

        repo.update_flags("dQw4w9WgXcQ", transcribed=True, qa_extracted=True)

        result = repo.get_by_id("dQw4w9WgXcQ")
        assert result.transcribed   == True
        assert result.qa_extracted  == True
        assert result.embedded      == False   # untouched

    def test_update_flags_ignores_none_values(self, override_db_engine):
        repo = AudioMetadataRepository()
        repo.save(make_audio())

        # only update transcribed
        repo.update_flags("dQw4w9WgXcQ", transcribed=True)

        result = repo.get_by_id("dQw4w9WgXcQ")
        assert result.transcribed  == True
        assert result.qa_extracted == False   # untouched
        assert result.embedded     == False   # untouched


# ── Transcript Repository Tests ───────────────────────────────────────────────

@pytest.mark.integration
class TestTranscriptRepository:

    def test_save_and_get_by_video_id(self, override_db_engine):
        audio_repo      = AudioMetadataRepository()
        transcript_repo = TranscriptRepository()

        audio_repo.save(make_audio())
        transcript = make_transcript()
        transcript_repo.save(transcript)

        result = transcript_repo.get_by_video_id("dQw4w9WgXcQ")

        assert result is not None
        assert result.video_id  == "dQw4w9WgXcQ"
        assert result.full_text == "والأعمام يسقطون..."
        assert result.language  == "ar"

    def test_exists_returns_true_after_save(self, override_db_engine):
        audio_repo      = AudioMetadataRepository()
        transcript_repo = TranscriptRepository()

        audio_repo.save(make_audio())
        transcript_repo.save(make_transcript())

        assert transcript_repo.exists("dQw4w9WgXcQ") is True

    def test_exists_returns_false_when_not_saved(self, override_db_engine):
        repo = TranscriptRepository()

        assert repo.exists("nonexistent_video") is False

    def test_get_by_video_id_returns_none_when_not_found(self, override_db_engine):
        repo = TranscriptRepository()

        result = repo.get_by_video_id("nonexistent_video")
        assert result is None


# ── QAPair Repository Tests ───────────────────────────────────────────────────

@pytest.mark.integration
class TestQAPairRepository:

    def test_save_batch_and_get_by_video_id(self, override_db_engine):
        audio_repo      = AudioMetadataRepository()
        transcript_repo = TranscriptRepository()
        qa_repo         = QAPairRepository()

        audio_repo.save(make_audio())
        transcript = make_transcript()
        transcript_repo.save(transcript)

        qa_pairs = [
            make_qa_pair("dQw4w9WgXcQ", transcript.id),
            make_qa_pair("dQw4w9WgXcQ", transcript.id),
        ]
        qa_repo.save_batch(qa_pairs)

        results = qa_repo.get_by_video_id("dQw4w9WgXcQ")

        assert len(results) == 2
        assert all(q.video_id == "dQw4w9WgXcQ" for q in results)

    def test_get_unembedded_returns_pairs_without_embedding_id(self, override_db_engine):
        audio_repo      = AudioMetadataRepository()
        transcript_repo = TranscriptRepository()
        qa_repo         = QAPairRepository()

        audio_repo.save(make_audio())
        transcript = make_transcript()
        transcript_repo.save(transcript)

        qa1 = make_qa_pair("dQw4w9WgXcQ", transcript.id)
        qa2 = make_qa_pair("dQw4w9WgXcQ", transcript.id)
        qa2.embedding_id = "chroma_abc123"   # already embedded

        qa_repo.save_batch([qa1, qa2])

        results = qa_repo.get_unembedded()

        assert len(results) == 1
        assert results[0].id == qa1.id

    def test_update_embedding_id(self, override_db_engine):
        audio_repo      = AudioMetadataRepository()
        transcript_repo = TranscriptRepository()
        qa_repo         = QAPairRepository()

        audio_repo.save(make_audio())
        transcript = make_transcript()
        transcript_repo.save(transcript)

        qa = make_qa_pair("dQw4w9WgXcQ", transcript.id)
        qa_repo.save_batch([qa])

        qa_repo.update_embedding_id(qa.id, "chroma_xyz789")

        results = qa_repo.get_by_video_id("dQw4w9WgXcQ")
        assert results[0].embedding_id == "chroma_xyz789"

    def test_save_batch_empty_list(self, override_db_engine):
        """Saving an empty batch should not crash."""
        repo = QAPairRepository()
        repo.save_batch([])   # should complete silently