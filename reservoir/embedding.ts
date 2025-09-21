import { eventHandler, MessageHandlerBuilder } from "./handling";
import { Embedding, validateEmbedding } from "./parser";
import { saveTopicVector } from "./s3vectors";
import { getConfigRequired, printMessage } from "./utils";

const saveTopicEmbeddingToS3Vector = async (e: Embedding) => {
  await saveTopicVector(getConfigRequired('VECTOR_BUCKET_NAME'), getConfigRequired('VECTOR_INDEX_NAME'))(e.keyword, e.embedding)
}

const EmbeddingHandler = new MessageHandlerBuilder<Embedding>()
	.withValidator(validateEmbedding)
	.withHandler(printMessage)
	.withHandler(saveTopicEmbeddingToS3Vector)
	.withPublisher(async e => {})
	.build()

const EmbeddingEventHandler = eventHandler<Embedding>(EmbeddingHandler.handle.bind(EmbeddingHandler))

export const handler = EmbeddingEventHandler
