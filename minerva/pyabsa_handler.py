class  PyABSAWorker:
    def __init__(self):
        from pyabsa import AspectTermExtraction as ATEPC
        self.model = ATEPC.AspectExtractor('english', offline=True, from_flax=True)

    def process(self, text):
        return self.model.predict(text, save_result=False)
