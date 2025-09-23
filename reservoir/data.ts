import { APIGatewayProxyEventV2, APIGatewayProxyResultV2, Handler } from "aws-lambda";
import { EmbeddingModel, FlagEmbedding } from "fastembed";
import { querySimilarVectorsBuilder } from "./s3vectors";
import { getConfigRequired } from "./utils";
import { getBodyByDataId, getDataByTopic } from "./ddb";

const querySimilarVectors = querySimilarVectorsBuilder(
	getConfigRequired('VECTOR_BUCKET_NAME'),
	getConfigRequired('VECTOR_INDEX_NAME')
);

let embeddingModel: FlagEmbedding;

const embedQuery = async (text: string): Promise<number[]> => {
	if (!embeddingModel) {
		embeddingModel = await FlagEmbedding.init({
			model: EmbeddingModel.AllMiniLML6V2,
			cacheDir: '/tmp/flagembed_cache'
		});
	}
	const batches = embeddingModel.embed([text]);
	// i.e. a single batch with a single embedding
	for await (const batch of batches) {
		return Array.from(batch[0]) as number[];
	}
	return [];
}

interface ResponseData {
	topic: string;
	body: string;
	sentiment: number;
}

export const handler: Handler = async (event: APIGatewayProxyEventV2, context): Promise<APIGatewayProxyResultV2> => {
	console.log("Received event:", JSON.stringify(event, null, 2));
	try {
		const { query } = event.queryStringParameters ?? {}
		if (!query) {
			return {
				statusCode: 400,
				body: "Missing 'query' parameter",
			};
		}

		const vector = await embedQuery(query);
		const similar = await querySimilarVectors(vector);

		const topics = similar?.map(v => v.key).filter(k => k) as string[] || [];

		const data = await Promise.all(topics.map(async t => ({
			[t]: await getDataByTopic(t)
		})))

		const flatData = data.flatMap(topicObj =>
			Object.values(topicObj)[0]
		);

		const nonNullData = flatData.filter(d => d != null);

		const responseBody: ResponseData[] = await Promise.all(nonNullData.map(async d => ({
			topic: d.topicId,
			body: await getBodyByDataId(d.dataId) ?? `[Content not found for dataId ${d.dataId}]`,
			sentiment: d.sentiment
		})))

		return {
			statusCode: 200,
			body: JSON.stringify(responseBody),
		};
	} catch (error) {
		console.error("Error processing event:", error);
		return { statusCode: 500, body: "Internal Server Error" };
	}

}
