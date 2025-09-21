import { PutVectorsCommand, QueryVectorsCommand, S3VectorsClient } from "@aws-sdk/client-s3vectors";

const s3VectorsClient = new S3VectorsClient()

export const saveTopicVector = (vectorBucketName: string, indexName: string) => async (topic: string, vector: number[]) => {
	const cmd = new PutVectorsCommand({
		vectorBucketName,
		indexName,
		vectors: [
			{
				key: topic,
				data: {
					float32: vector
				}
			}
		]
	})
	await s3VectorsClient.send(cmd)
}

export const querySimilarVectorsBuilder = (vectorBucketName: string, indexName: string) => async (vector: number[]) => {
	const cmd = new QueryVectorsCommand({
		vectorBucketName,
		indexName,
		topK: 5,
		queryVector: {
			float32: vector
		}
	})
	const res = await s3VectorsClient.send(cmd)
	res.vectors?.forEach(v => console.log(v))
	return res.vectors
}
