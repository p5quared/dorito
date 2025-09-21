import { Handler } from "aws-lambda";
import { EmbeddingModel, FlagEmbedding } from "fastembed";
import { querySimilarVectorsBuilder } from "./s3vectors";
import { getConfigRequired } from "./utils";
import { getDataByTopic } from "./ddb";

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
			model: EmbeddingModel.AllMiniLML6V2,
			cacheDir: '/tmp/flagembed_cache'
		});

	}
	console.log(`Finding topics similar to: ${event.topic}`);
	const batches = embeddingModel.embed([event.topic]);
	let allKeys: string[] = [];
	for await (const batch of batches) {
		const vecs = await querySimilarVectors(Array.from(batch[0]) as number[]);
		vecs?.forEach(v => {
		if (v.key) {
			allKeys.push(v.key);
		}})
	}

  const data = allKeys.flatMap(async e => await getDataByTopic(e))
  console.log(data)
  return data ?? [];
}
