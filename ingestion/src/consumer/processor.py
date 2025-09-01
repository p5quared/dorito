import re
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer
from typing import Any, Dict
from shared.types import CommentData, PostData
from shared.interfaces import DataProcessor, Logger


class PrintProcessor(DataProcessor):
    """Simple processor that logs data"""

    def __init__(self, logger: Logger):
        self._logger = logger

    def process(self, data: CommentData | PostData) -> Dict[str, Any]:
        self._logger.info(f"Processing message: {data}")
        return data.to_dict()  # pyright: ignore


class FinancialRelevanceProcessor(DataProcessor):
    """Processor that filters content for financial relevance using FinBERT"""

    def __init__(
        self,
        logger: Logger,
        model_name: str = "ProsusAI/finbert",
        threshold: float = 0.8,
    ):
        self._logger = logger
        self._threshold = threshold
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
        self._logger.info(
            f"Initialized FinancialRelevanceProcessor with model: {model_name}"
        )

    def process(self, data: CommentData | PostData) -> Dict[str, Any]:
        if not data.body or data.body.strip() == "":
            self._logger.debug("Post has no body, skipping...")
            return {}

        if not self._is_financially_relevant(data.body):
            self._logger.debug("Post has no financial relevancy")
            return {}

        self._logger.debug(f"\n{data.body}\n")
        return data.to_dict()  # pyright: ignore

    def _is_financially_relevant(self, text: str) -> bool:
        """Check if text is financially relevant using FinBERT"""
        inputs = self.tokenizer(
            text, return_tensors="pt", truncation=True, max_length=512
        )
        outputs = self.model(**inputs)
        score = torch.nn.functional.softmax(outputs.logits, dim=1)[0][1]
        return float(score) >= self._threshold

    @staticmethod
    def get_sentences(text: str) -> list[str]:
        """Split text into sentences"""
        sentence_endings = re.compile(r"[.!?]")
        sentences = sentence_endings.split(text)
        return [s.strip() for s in sentences if s.strip()]
