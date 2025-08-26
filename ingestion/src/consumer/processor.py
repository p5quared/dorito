import re
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer
from shared.types import CommentData, PostData
from shared.utils import LoggingMixin


class Writer:
    def save(self, data):
        return None


class Processor:
    def process(self, data) -> dict:
        return {}


class PrintProcessor(Processor, LoggingMixin):
    def process(self, data):
        super().log_info(f"Processing message: {data}")
        return data


class RedditDataProcessor(Processor, LoggingMixin):
    def __init__(self):
        super().__init__()
        self.tokenizer = AutoTokenizer.from_pretrained("ProsusAI/finbert")
        self.model = AutoModelForSequenceClassification.from_pretrained(
            "ProsusAI/finbert"
        )
        super().log_info("Initialized RedditDataProcessor")

    def process(self, data: CommentData | PostData) -> dict:
        if not data.body or data.body.strip() == "":
            super().log_debug("Post has no body, skipping...")
            return {}

        if not self.is_financially_relevant(data.body):
            super().log_debug("Post has no financial relevancy")
            return {}
        super().log_debug(f"\n{data.body}\n")
        return data.to_dict()  # pyright: ignore

    def is_financially_relevant(self, text: str) -> bool:
        inputs = self.tokenizer(
            text, return_tensors="pt", truncation=True, max_length=512
        )
        outputs = self.model(**inputs)
        score = torch.nn.functional.softmax(outputs.logits, dim=1)[0][1]
        return score >= 0.8  # pyright: ignore (it works! I've seen it work!  I swear!!!!)

    @staticmethod
    def get_sentences(text: str) -> list[str]:
        sentence_endings = re.compile(r"[.!?]")
        sentences = sentence_endings.split(text)
        return [s.strip() for s in sentences if s.strip()]
