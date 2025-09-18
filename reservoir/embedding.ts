import { eventHandler, MessageHandlerBuilder } from "./handling";
import { EmbeddingProducedEvent, validateEmbeddingProducedEvent } from "./parser";
import { printMessage } from "./utils";

const EmbeddingHandler = new MessageHandlerBuilder<EmbeddingProducedEvent>()
	.withValidator(validateEmbeddingProducedEvent)
	.withHandler(printMessage)
	.build()

const EmbeddingEventHandler = eventHandler<EmbeddingProducedEvent>(EmbeddingHandler.handle.bind(EmbeddingHandler))

export const handler = EmbeddingEventHandler
