from typing import List, Tuple

from message_types import KeyWordResult


class KeywordWorker:
    def __init__(self):
        from keybert import KeyBERT
        self.model = KeyBERT()
    def process(self, data: str):
        return self.model.extract_keywords(data, keyphrase_ngram_range=(1, 2), use_maxsum=True, top_n=3)

class KeywordResultTransformer:
    def transform(self, result: List[Tuple[str, float]]) -> List[KeyWordResult]:
        return [KeyWordResult(keyword=keyword, confidence=score) for keyword, score in result]
