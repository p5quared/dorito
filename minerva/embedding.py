class EmbeddingWorker:
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        from fastembed import TextEmbedding
        self.model = TextEmbedding(model_name=model_name)
    def embed(self, text: str):
        return list(list(self.model.embed(text))[0])
