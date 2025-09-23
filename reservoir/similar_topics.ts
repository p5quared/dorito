import { APIGatewayProxyEventV2, APIGatewayProxyResultV2, Handler } from "aws-lambda";
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

export const handler: Handler = async (event: APIGatewayProxyEventV2, context): Promise<APIGatewayProxyResultV2> => {
	try {
		console.log("Received event:", JSON.stringify(event, null, 2));

		const inputBody: SimilarTopicsRequest = event.body ? JSON.parse(event.body) : {};
		if (!embeddingModel) {
			embeddingModel = await FlagEmbedding.init({
				model: EmbeddingModel.AllMiniLML6V2,
				cacheDir: '/tmp/flagembed_cache'
			});

		}
		console.log(`Finding topics similar to: ${inputBody.topic}`);
		const batches = embeddingModel.embed([inputBody.topic]);
		// NOTE: keys are the topic names in s3Vector
		let allKeys: string[] = [];
		for await (const batch of batches) {
			const vecs = await querySimilarVectors(Array.from(batch[0]) as number[]);
			vecs?.forEach(v => {
				if (v.key) {
					allKeys.push(v.key);
				}
			})
		}

		
		const result =await Promise.all( allKeys.map(async k => ({
			[k]: await getDataByTopic(k)
		})))

		for (const key of allKeys) {
			console.log(`Similar topic: ${key}`);
			const correspondingData = await getDataByTopic(key);
			console.log(correspondingData);
		}
		return {
			statusCode: 200,
			body: JSON.stringify(result),
		};
	} catch (error) {
		console.error("Error processing event:", error);
		return { statusCode: 500, body: "Internal Server Error" };
	}

}
