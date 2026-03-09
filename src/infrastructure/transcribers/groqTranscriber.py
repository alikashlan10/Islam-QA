from groq import Groq
from groq import APIStatusError, APIConnectionError, RateLimitError

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)
import logging

from src.application.interfaces.transcriber import Transcriber
from src.domain.models.transcript import Transcript, TranscriptSegment
from src.logger.logger import setup_logger
from src.config import AppConfig

logger = setup_logger(__name__)
config = AppConfig()


class GroqTranscriber(Transcriber):
    """
    Transcriber implementation backed by Groq's hosted Whisper API.
    """

    def __init__(
        self,
        api_key: str = config.GROQ_API_KEY,
        model: str = config.GROQ_WHISPER_MODEL,
        language: str = "ar",
    ) -> None:
        self._client   = Groq(api_key=api_key)
        self._model    = model
        self._language = language


    @retry(
        retry=retry_if_exception_type((
            RateLimitError,
            APIConnectionError,
        )),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        stop=stop_after_attempt(3),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True
    )
    def _invoke_api(self, audio_file) -> object:
        """
        Isolated API call with retry logic.
        Retries on:
          - RateLimitError    : 429 — too many requests
          - APIConnectionError: transient network issues
        Does NOT retry on:
          - APIStatusError (4xx): bad request, wrong file format, auth error
            these are bugs/config issues — retrying won't help
        """    
        return self._client.audio.transcriptions.create(
            file=audio_file,
            model=self._model,
            language=self._language,
            response_format="verbose_json",
        )



    def transcribe(self, audio_path: str) -> Transcript:
        logger.info(f"Transcribing audio file: {audio_path}")

        try:
            with open(audio_path, "rb") as audio_file:
                response = self._invoke_api(audio_file)

        except FileNotFoundError:
            logger.error(f"Audio file not found: {audio_path}")
            raise
        except RateLimitError:
            logger.error("Groq rate limit hit after all retries.")
            raise
        except APIConnectionError:
            logger.error("Groq API connection failed after all retries.")
            raise
        except APIStatusError as e:
            logger.error(f"Groq API error {e.status_code}: {e.message}")
            raise

        logger.info(f"Transcription completed — detected language: {response.language}")

        segments = [
            TranscriptSegment(
                text=segment['text'].strip(),
                start=segment['start'],
                end=segment['end'],
                speaker=None,
            )
            for segment in response.segments
        ]

        return Transcript(
            full_text=response.text.strip(),
            segments=segments,
            language=response.language,
            source_audio_path=audio_path,
        )