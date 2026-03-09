"""
Unit Tests for GroqTranscriber
================================
Run with: pytest test_groq_transcriber.py -v
"""

import pytest
from unittest.mock import MagicMock, patch, mock_open

from groq import APIStatusError, APIConnectionError, RateLimitError

from src.infrastructure.transcribers.groqTranscriber import GroqTranscriber
from src.domain.models.transcript import Transcript, TranscriptSegment


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_mock_segment(text: str, start: float, end: float) -> dict:
    """
    Builds a fake Groq API segment object.
    Groq returns objects with attributes, not dicts — MagicMock mimics that.
    """
    return {
        "text":  text,
        "start": start,
        "end":   end,
    }


def make_mock_response(
    text: str = "Full transcript text.",
    language: str = "ar",
    segments: list = None
) -> MagicMock:
    """
    Builds a fake Groq API transcription response.
    """
    response = MagicMock()
    response.text     = text
    response.language = language
    response.segments = segments or [
        make_mock_segment("First segment.", 0.0, 3.5),
        make_mock_segment("Second segment.", 3.5, 7.0),
    ]
    return response


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_groq_client():
    """
    Patches the Groq client so no real API calls are made.
    Returns the mock client instance so tests can configure its behavior.
    """
    with patch("src.infrastructure.transcribers.groqTranscriber.Groq") as mock_groq_class:
        mock_client = MagicMock()
        mock_groq_class.return_value = mock_client
        yield mock_client


@pytest.fixture
def transcriber(mock_groq_client):
    """
    Creates a GroqTranscriber with a mocked Groq client.
    mock_groq_client fixture runs first — client is already patched.
    """
    return GroqTranscriber(api_key="fake-api-key")


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestTranscribeHappyPath:

    def test_returns_transcript_object(self, transcriber, mock_groq_client):
        """
        Happy path — valid API response maps correctly to a Transcript domain object.
        """
        mock_groq_client.audio.transcriptions.create.return_value = make_mock_response()

        # mock_open simulates opening a file without needing a real file on disk
        with patch("builtins.open", mock_open(read_data=b"fake audio bytes")):
            result = transcriber.transcribe("audio/lecture.mp3")

        assert isinstance(result, Transcript)
        assert result.full_text == "Full transcript text."
        assert result.language  == "ar"
        assert result.source_audio_path == "audio/lecture.mp3"

    def test_segments_mapped_correctly(self, transcriber, mock_groq_client):
        """
        Verify each segment's text, start, and end are correctly mapped.
        """
        mock_groq_client.audio.transcriptions.create.return_value = make_mock_response(
            segments=[
                make_mock_segment("  Hello world.  ", 0.0, 2.5),   # note leading/trailing spaces
                make_mock_segment("Second line.", 2.5, 5.0),
            ]
        )

        with patch("builtins.open", mock_open(read_data=b"audio")):
            result = transcriber.transcribe("audio/lecture.mp3")

        assert len(result.segments) == 2

        assert result.segments[0].text  == "Hello world."   # stripped ✓
        assert result.segments[0].start == 0.0
        assert result.segments[0].end   == 2.5

        assert result.segments[1].text  == "Second line."
        assert result.segments[1].start == 2.5
        assert result.segments[1].end   == 5.0

    def test_speaker_is_always_none(self, transcriber, mock_groq_client):
        """
        Groq Whisper doesn't support diarization — speaker must always be None.
        """
        mock_groq_client.audio.transcriptions.create.return_value = make_mock_response()

        with patch("builtins.open", mock_open(read_data=b"audio")):
            result = transcriber.transcribe("audio/lecture.mp3")

        assert all(segment.speaker is None for segment in result.segments)

    def test_full_text_is_stripped(self, transcriber, mock_groq_client):
        """
        Leading/trailing whitespace in the full text should be stripped.
        """
        mock_groq_client.audio.transcriptions.create.return_value = make_mock_response(
            text="  \n  Some transcript text.  \n  "
        )

        with patch("builtins.open", mock_open(read_data=b"audio")):
            result = transcriber.transcribe("audio/lecture.mp3")

        assert result.full_text == "Some transcript text."


class TestTranscribeErrorHandling:

    def test_raises_file_not_found(self, transcriber):
        """
        If the audio file doesn't exist, FileNotFoundError should bubble up.
        We don't mock open here — we let it actually fail.
        """
        with pytest.raises(FileNotFoundError):
            transcriber.transcribe("non_existent_file.mp3")

    def test_raises_after_rate_limit_retries(self, transcriber, mock_groq_client):
        """
        RateLimitError should be retried by tenacity then bubble up after exhaustion.
        """
        mock_groq_client.audio.transcriptions.create.side_effect = RateLimitError(
            message="rate limit exceeded",
            response=MagicMock(status_code=429),
            body={}
        )

        with patch("builtins.open", mock_open(read_data=b"audio")):
            with pytest.raises(RateLimitError):
                transcriber.transcribe("audio/lecture.mp3")

    def test_raises_on_connection_error(self, transcriber, mock_groq_client):
        """
        APIConnectionError (network failure) should be retried then bubble up.
        """
        mock_groq_client.audio.transcriptions.create.side_effect = APIConnectionError(
            request=MagicMock()
        )

        with patch("builtins.open", mock_open(read_data=b"audio")):
            with pytest.raises(APIConnectionError):
                transcriber.transcribe("audio/lecture.mp3")

    def test_raises_immediately_on_api_status_error(self, transcriber, mock_groq_client):
        """
        APIStatusError (4xx — bad file, auth error) should raise immediately.
        These are config/usage bugs — retrying won't help.
        """
        mock_groq_client.audio.transcriptions.create.side_effect = APIStatusError(
            message="invalid file format",
            response=MagicMock(status_code=400),
            body={}
        )

        with patch("builtins.open", mock_open(read_data=b"audio")):
            with pytest.raises(APIStatusError):
                transcriber.transcribe("audio/lecture.mp3")

    def test_rate_limit_retries_before_raising(self, transcriber, mock_groq_client):
        """
        Verify tenacity retries multiple times before giving up on RateLimitError.
        side_effect list: first two calls fail, third succeeds.
        """
        mock_groq_client.audio.transcriptions.create.side_effect = [
            RateLimitError(message="rate limit", response=MagicMock(status_code=429), body={}),
            RateLimitError(message="rate limit", response=MagicMock(status_code=429), body={}),
            make_mock_response(),   # third attempt succeeds
        ]

        with patch("builtins.open", mock_open(read_data=b"audio")):
            result = transcriber.transcribe("audio/lecture.mp3")

        assert mock_groq_client.audio.transcriptions.create.call_count == 3
        assert isinstance(result, Transcript)