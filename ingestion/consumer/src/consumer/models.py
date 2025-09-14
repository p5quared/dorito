import time
from shared.io import LoggingMixin
from keybert import KeyBERT

class MinervaKeyBERTModel(LoggingMixin):
    def __init__(self, config):
        super().__init__(config)
        self.kw_model = KeyBERT()

    def infer(self, data: str)-> list[tuple[str, float]]:
        start_time = time.time()
        raw_data = self.kw_model.extract_keywords(data, keyphrase_ngram_range=(1, 3), stop_words='english')
        self.log_info(f"Ran inference in {time.time() - start_time:.2f}s")
        # assert that the data is (string, float) tuple
        # for some reason KeyBERT can return other types
        results = []
        for item in raw_data:
            if isinstance(item, tuple) and len(item) == 2:
                keyword, confidence = item
            else:
                self.log_warning(f"Unexpected item format: {item}")
                continue
            if isinstance(keyword, str) and isinstance(confidence, float):
                results.append(item)
            else:
                self.log_warning(f"Unexpected types in tuple: {item}")
        return results

