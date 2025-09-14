from typing import Any, Callable, Protocol


class DataModel(Protocol):
    def validate(self, data: Any) -> bool:
        ...


class Worker(Protocol):
    def process(self, data: Any) -> Any:
        ...


class ResultTransformer(Protocol):
    def transform(self,  result: Any) -> Any:
        ...


class Publisher(Protocol):
    def publish(self, data: Any) -> None:
        ...


class MinervaApplication:
    @staticmethod
    def handler(
        input_model: DataModel,
        worker: Worker,
        result_transformer: ResultTransformer,
        publisher: Publisher,
        data: Any
    ) -> None:
        if not input_model.validate(data):
            raise ValueError("Input data does not match required format")
        
        result = worker.process(data)
        transformed_result = result_transformer.transform(result)
        publisher.publish(transformed_result)

    @staticmethod
    def create_handler(
        input_model,
        worker,
        result_transformer,
        publisher,
    ) -> Callable[[Any], None]:
        def handler(data: Any) -> None:
            MinervaApplication.handler(
                input_model,
                worker,
                result_transformer,
                publisher,
                data
            )
        return handler
