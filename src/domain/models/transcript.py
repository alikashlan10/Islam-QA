from pydantic import BaseModel
from typing import List

# domain/models/transcript.py
class TranscriptSegment(BaseModel):
    text: str
    start: float          # seconds
    end: float            # seconds
    speaker: str | None   # from diarization, if available

class Transcript(BaseModel):
    full_text: str
    segments: List[TranscriptSegment]
    language: str | None
    source_audio_path: str