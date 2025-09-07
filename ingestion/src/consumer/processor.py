import re
from sentence_transformers import SentenceTransformer
import sqlite3
import pandas as pd
import torch
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from typing import Any, Dict
from shared.types import CommentData, PostData
from shared.interfaces import DataProcessor, ConfigProvider
from shared.utils import LoggingMixin


class PrintProcessor(LoggingMixin, DataProcessor):
    """Simple processor that logs data"""

    def __init__(self, config: ConfigProvider):
        super().__init__(config=config)
        self.n_processed = 0

    def process(self, data: CommentData | PostData) -> Dict[str, Any]:
        self.n_processed += 1
        # self.log_info(f"Processing message: {data}")
        self.log_info(f"Processed count: {self.n_processed}\n")
        return data.to_dict()  # pyright: ignore


class FinancialRelevanceProcessor(LoggingMixin, DataProcessor):
    """Processor that filters content for financial relevance using FinBERT"""

    def __init__(
        self,
        config: ConfigProvider,
        model_name: str = "ProsusAI/finbert",
        threshold: float = 0.3,
    ):
        super().__init__(config=config)
        self._threshold = threshold
        self._init_evaluation_dataset()
        self.log_info(
            f"Initialized FinancialRelevanceProcessor with model: {model_name}"
        )

    def process(self, data: CommentData | PostData) -> Dict[str, Any]:
        if not data.body or data.body.strip() == "":
            self.log_debug("Post has no body, skipping...")
            return {}

        if not self._is_financially_relevant(data.body):
            self.log_info(f"\nbad:\n{data.body}\n")
            self.log_debug("Content not financially relevant, skipping...")
            return {}

        self.log_info(f"\ngood:\n{data.body}\n")
        return data.to_dict()  # pyright: ignore

    def _is_financially_relevant(self, text: str) -> bool:
        """Check if text is financially relevant using cosine similarity"""
        text_embedding = self.embedder.encode([text], show_progress_bar=False)
        
        similarities = cosine_similarity(text_embedding, self.finance_embeddings)
        max_similarity = similarities.max()
        
        self.log_info(f"Max similarity: {max_similarity}")
        return max_similarity >= self._threshold

    def _init_evaluation_dataset(self):
        """Load evaluation data from a text file"""
        self.log_info("Loading financial corpus from database...")
        conn = sqlite3.connect("finance_corpus.db")
        finance_df = pd.read_sql_query("SELECT * FROM articles", conn)
        conn.close()

        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        self.finance_embeddings = self.embedder.encode(finance_df['body'], show_progress_bar=False)
    

    @staticmethod
    def get_sentences(text: str) -> list[str]:
        """Split text into sentences"""
        sentence_endings = re.compile(r"[.!?]")
        sentences = sentence_endings.split(text)
        return [s.strip() for s in sentences if s.strip()]
