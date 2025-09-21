import { Handler } from "aws-lambda";
import { getConfigRequired } from "../utils";
import { querySimilarVectorsBuilder } from "../s3vectors";
import { EmbeddingModel, FlagEmbedding } from "fastembed";

interface SimilarTopicsRequest {
	topic: string;
}

const querySimilarVectors = querySimilarVectorsBuilder(
	getConfigRequired('VECTOR_BUCKET_NAME'),
	getConfigRequired('VECTOR_INDEX_NAME')
);

let embeddingModel: FlagEmbedding;

export const handler: Handler = async (event: SimilarTopicsRequest, context) => {
	if (!embeddingModel) {
		embeddingModel = await FlagEmbedding.init({
			model: EmbeddingModel.AllMiniLML6V2
		});

	}
	console.log(`Finding topics similar to: ${event.topic}`);
	const embedding = embeddingModel.embed([event.topic]);
	console.log(embedding);
	for await (const vec of embedding) {
		await querySimilarVectors(vec[0]);
	}
}
