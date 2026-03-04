"""
Unit Tests for GeminiQAExtractor
=================================
Run with:  pytest geminiQAExtractorTest.py -v

Key concepts used:
- pytest.fixture     : reusable setup shared across tests
- unittest.mock.patch: replace real dependencies with fakes during tests
- pytest.raises      : assert that a specific exception is thrown
"""

import pytest
from unittest.mock import MagicMock, patch
from langchain_core.exceptions import OutputParserException
import google.api_core.exceptions as google_exceptions

from src.infrastructure.extractors.geminiQAExtractor import GeminiQAExtractor, QAListSchema,QAPairSchema

from src.domain.models.qaPair import QAPair


# ── Fixtures ──────────────────────────────────────────────────────────────────
#
# A fixture is a reusable piece of setup that pytest automatically injects
# into any test function that declares it as a parameter.
# Instead of repeating setup code in every test, you define it once here.

@pytest.fixture
def mock_dependencies():
    """
    Patches out ALL external dependencies so no real API calls are made.
    """
    with patch("src.infrastructure.extractors.geminiQAExtractor.ChatGoogleGenerativeAI") as mock_llm_class, \
         patch("src.infrastructure.extractors.geminiQAExtractor.OutputFixingParser") as mock_fixing_parser_class, \
         patch("src.infrastructure.extractors.geminiQAExtractor.AppConfig") as mock_config_class:

        # Configure the fake config to return dummy values
        mock_config = MagicMock()
        mock_config.GEMINI_API_KEY   = "fake-api-key"
        mock_config.GEMINI_MODEL_NAME = "gemini-1.5-flash"
        mock_config_class.return_value = mock_config

        # mock_llm_class() is what gets called inside __init__
        # .return_value is the instance that comes back from that call
        mock_llm_instance = MagicMock()
        mock_llm_class.return_value = mock_llm_instance

        # Same for the OutputFixingParser
        mock_parser_instance = MagicMock()
        mock_fixing_parser_class.from_llm.return_value = mock_parser_instance

        yield {
            "llm":    mock_llm_instance,
            "parser": mock_parser_instance,
        }


@pytest.fixture
def extractor(mock_dependencies):
    """
    Creates a GeminiQAExtractor instance using the mocked dependencies above.
    Any test that uses this fixture gets a clean extractor with no real LLM.
    """
    return GeminiQAExtractor()


@pytest.fixture
def sample_qa_schema():
    """
    A reusable fake LLM response — a QAListSchema with two QA pairs.
    Used in tests that need to simulate a successful LLM extraction.
    """
    return QAListSchema(pairs=[
        QAPairSchema(
            question="What is photosynthesis?",
            answer="Photosynthesis is the process by which plants convert sunlight into glucose."
        ),
        QAPairSchema(
            question="What do plants need for photosynthesis?",
            answer="Plants need sunlight, water, and carbon dioxide."
        ),
    ])



class TestExtractHappyPath:
    """Tests for normal, successful extraction scenarios."""

    def test_returns_list_of_qa_pairs(self, extractor, sample_qa_schema):
        """
        test that chain succesfully returns list of QAPair
        """
        # Tell the fake chain what to return when .invoke() is called
        extractor._invoke_chain = MagicMock(return_value=sample_qa_schema)

        result = extractor.extract("Photosynthesis converts sunlight into glucose...")

        # Assert the return type and length
        assert isinstance(result, list)
        assert len(result) == 2

        # Assert the contents are proper domain objects with correct values
        assert all(isinstance(pair, QAPair) for pair in result)
        assert result[0].question == "What is photosynthesis?"
        assert result[0].answer   == "Photosynthesis is the process by which plants convert sunlight into glucose."

    def test_returns_empty_list_when_no_pairs_found(self, extractor):
        """
        When the LLM finds no QA pairs in the text, it returns pairs: [].
        extract() should propagate this as an empty list, not raise an error.
        """
        extractor._invoke_chain = MagicMock(return_value = QAListSchema(pairs=[]))

        result = extractor.extract("This is just some random filler text with no QA content.")

        assert result == []

    def test_chain_receives_correct_text(self, extractor, sample_qa_schema):
        """
        Verify that the text is passed through to the chain correctly.
        This tests the wiring, not just the output.
        """
        extractor._invoke_chain = MagicMock(return_value=sample_qa_schema)


        input_text = "What is gravity? Gravity is the force of attraction between masses."
        extractor.extract(input_text)

        # Assert the chain was called with the exact text we passed in
        extractor._invoke_chain.assert_called_once_with(input_text)


class TestExtractEdgeCases:
    """Tests for boundary conditions and invalid inputs."""

    @pytest.mark.parametrize("bad_input", [
        "",           # empty string
        "   ",        # only whitespace
        "\n\t\n",     # only newlines and tabs
    ])
    def test_empty_or_blank_text_returns_empty_list(self, extractor, bad_input):
        """
        tests for three empty variants.
        """
        extractor._chain = MagicMock()

        result = extractor.extract(bad_input)

        assert result == []
        # The LLM chain should never have been called for empty input
        extractor._chain.invoke.assert_not_called()


class TestExtractErrorHandling:


    def test_raises_on_rate_limit_after_retries(self, extractor):
        """
        When Gemini returns a 429 (ResourceExhausted), tenacity retries.
        After all retries are exhausted, the exception should bubble up.
        """
        extractor._invoke_chain = MagicMock(side_effect = google_exceptions.ResourceExhausted("Rate limit exceeded"))
        

        # If the exception is NOT raised, the test fails.
        with pytest.raises(google_exceptions.ResourceExhausted):
            extractor.extract("Some valid text about machine learning.")


    def test_raises_on_output_parser_failure(self, extractor):
        """
        When the LLM returns output that can't be parsed even after
        OutputFixingParser's self-correction attempts, OutputParserException
        should bubble up from extract().
        """
        extractor._chain = MagicMock()
        extractor._chain.invoke.side_effect = OutputParserException("Could not parse LLM output")

        with pytest.raises(OutputParserException):
            extractor.extract("Some valid text.")


    def test_rate_limit_retries_before_raising(self, extractor):
        """
        Verify that the chain is called MULTIPLE times before giving up.
        This confirms tenacity retry logic is actually running.
        """
        extractor._chain = MagicMock()

        # Fail twice, then succeed on the third attempt
        extractor._chain.invoke.side_effect = [
            google_exceptions.ResourceExhausted("Retry 1"),
            google_exceptions.ResourceExhausted("Retry 2"),
            QAListSchema(pairs=[
                QAPairSchema(question="What is ML?", answer="Machine learning.")
            ])
        ]

        result = extractor.extract("Machine learning is a subset of AI.")

        # Should have been called 3 times total (2 failures + 1 success)
        assert extractor._chain.invoke.call_count == 3
        assert len(result) == 1
        assert result[0].question == "What is ML?"