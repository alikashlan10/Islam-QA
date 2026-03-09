import pytest
from src.infrastructure.transcribers.groqTranscriber import GroqTranscriber

# run only when explicitly requested: pytest -m integration
@pytest.mark.integration
def test_real_transcription():
    """
    Hits the real Groq API with a real audio file.
    Requires GROQ_API_KEY in .env and a real audio file.
    """
    transcriber = GroqTranscriber()
    result = transcriber.transcribe("src/tests/fixtures/sample_audio.mp3")

    assert result.full_text != ""
    assert len(result.segments) > 0
    assert result.language is not None