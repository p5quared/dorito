import { eventHandler, MessageHandlerBuilder } from "./handling";
import { EmbeddingProducedEvent, validateEmbeddingProducedEvent } from "./parser";
import { saveTopicVector } from "./s3vectors";
import { getConfigRequired, printMessage } from "./utils";

const saveTopicEmbeddingToS3Vector = async (e: EmbeddingProducedEvent) => {
  await saveTopicVector(getConfigRequired('VECTOR_BUCKET_NAME'), getConfigRequired('VECTOR_INDEX_NAME'))(e.data.keyword, e.data.vector)
}

const EmbeddingHandler = new MessageHandlerBuilder<EmbeddingProducedEvent>()
	.withValidator(validateEmbeddingProducedEvent)
	.withHandler(printMessage)
	.withHandler(saveTopicEmbeddingToS3Vector)
	.build()

const EmbeddingEventHandler = eventHandler<EmbeddingProducedEvent>(EmbeddingHandler.handle.bind(EmbeddingHandler))

export const handler = EmbeddingEventHandler
