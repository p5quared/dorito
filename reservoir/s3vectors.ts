import { PutVectorsCommand, S3VectorsClient } from "@aws-sdk/client-s3vectors";

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
