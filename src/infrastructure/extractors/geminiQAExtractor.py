from typing import List

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_classic.output_parsers.fix import OutputFixingParser
from langchain_core.exceptions import OutputParserException

import google.api_core.exceptions as google_exceptions

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

from pydantic import BaseModel, Field
import logging

from src.application.interfaces.QAExtractor import QAExtractor
from src.domain.models.qaPair import QAPair
from src.logger.logger import setup_logger
from src.config import AppConfig


config = AppConfig()
logger = setup_logger(__name__)


class QAPairSchema(BaseModel):
    question: str = Field(description="A clear, self-contained question extracted from the text")
    answer: str   = Field(description="The corresponding answer extracted from the text")


class QAListSchema(BaseModel):
    pairs: List[QAPairSchema] = Field(description="List of question-answer pairs extracted from the text")



class GeminiQAExtractor(QAExtractor):
    """
    QAExtractor implementation backed by Google Gemini via LangChain.

    Chain:  prompt | llm (with structured output) | pydantic parser
    """


    SYSTEM_PROMPT = """You are an expert at extracting question-answer pairs from text.
Your job is to read the provided text and identify all meaningful QA pairs within it.

Rules:
- Each question must be self-contained and understandable without extra context.
- Each answer must be concise, accurate, and directly supported by the text.
- Do NOT invent information that is not present in the text.
- Ignore filler, off-topic remarks, or repeated content.
- If no clear QA pairs exist, return an empty list."""

    USER_PROMPT = """Extract all question-answer pairs from the following text:

<text>
{text}
</text>

{format_instructions}"""

    def __init__(self,api_key: str=config.GEMINI_API_KEY ,model: str =config.GEMINI_MODEL_NAME ,temperature: float = 0.0):

        
        self._base_parser = PydanticOutputParser(pydantic_object=QAListSchema)

        self._prompt = ChatPromptTemplate.from_messages([
            ("system", self.SYSTEM_PROMPT),
            ("human",  self.USER_PROMPT),
        ]).partial(format_instructions=self._base_parser.get_format_instructions())

        self._llm = ChatGoogleGenerativeAI(
            model=model,
            temperature=temperature,
            google_api_key=api_key,
        )

        self.parser = OutputFixingParser.from_llm(
            parser=self._base_parser,
            llm=self._llm,
            max_retries=2,
        )

        # LCEL chain
        self._chain = self._prompt | self._llm | self.parser

        
    @retry(
    retry=retry_if_exception_type((
        google_exceptions.ResourceExhausted,    # 429 rate limit
        google_exceptions.ServiceUnavailable,   # 503 transient error
    )),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    stop=stop_after_attempt(5),
    before_sleep=before_sleep_log(logger, logging.WARNING),  # logs each retry
    )
    def _invoke_chain(self , text:str) -> QAListSchema :
        return self._chain.invoke({"text":text})

         
        
    def extract(self, text: str) -> List[QAPair]:
        """
        Run the LangChain chain and map the parsed output to domain QAPair models.
        """
        if not text or not text.strip():
            logger.debug("Text provided is empty , returning an empty list !")
            return []
       
        try:
            result: QAListSchema = self._invoke_chain(text)
        except google_exceptions.ResourceExhausted:
            logger.error("Gemini rate limit hit after all retries.")
            raise
        except OutputParserException:
            logger.error("LLM returned unparseable output after self-correction attempts.")
            raise

        return [
            QAPair(question=pair.question, answer=pair.answer)
            for pair in result.pairs
        ]