import time

from shared.interfaces import MessageSource
from shared.utils import LoggingMixin
from shared.sns import DataProducedEvent, KeywordInferenceData

class Minerva(LoggingMixin):
    def __init__(self, queue: MessageSource, worker, config):
        super().__init__(config)
        self.message_queue: MessageSource = queue
        self.worker = worker

    def run(self):
        for message in self.message_queue.messages:
            try:
                start_time = time.time()
                
                self.worker.work(message)
                
                self.message_queue.delete_message(message)
                self.log_info(f"Processed message in {time.time() - start_time:.2f}s")
                
            except Exception as e:
                self.log_error(f"Failed to process message: {e}")


class MinervaWorker(LoggingMixin):
    """"
    By paramaterizing the model and publisher,
    we can easily work N model versions in Minerva that output the same format
    """
    def __init__(self, config, model, publisher):
        super().__init__(config)
        self.model = model
        self.publisher = publisher

    def can_process(self, message) -> bool:
        # Implement logic to determine if the message can be processed
        return True

    def package_result(self, id: str, result: tuple[str, float]) -> KeywordInferenceData:
        return KeywordInferenceData(
            source_id=id,
            keyword=result[0],
            confidence=result[1]
        )
    
    def work(self, event: DataProducedEvent):
        if not self.can_process(event):
            self.log_warning("Skipping message", event)
            return
        try:
            start_time = time.time()
            
            result = self.model.infer(event.data.body)
            msg = self.package_result(event.data.id, result)
            self.publisher.publish(msg)

            self.log_info(f"Processed message in {time.time() - start_time:.2f}s")
        except Exception as e:
            self.log_error(f"Failed to process message: {e}")
