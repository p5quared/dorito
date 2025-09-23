import { DynamoDBClient } from "@aws-sdk/client-dynamodb";
import { DynamoDBDocumentClient } from "@aws-sdk/lib-dynamodb";
import { any, Entity, item, number, PutItemCommand, QueryCommand, string, Table } from "dynamodb-toolbox";
import { PyABSAProducedEvent, RawDataProducedEvent } from "./parser";

const ddbClient = new DynamoDBClient()
const documentClient = DynamoDBDocumentClient.from(ddbClient)

// // Raw data item
// {
//   "PK": "RAW_DATA#12345",
//   "SK": "METADATA",
//   "data": { id, reddit_type, subreddit, body },
//   "source_date": "2024-01-15T10:30:00Z"
// }
//
// // Topic item
// {
//   "PK": "TOPIC#finance",
//   "SK": "METADATA", 
//   "topic_name": "Financial Analysis",
//   "description": "Financial market data and analysis"
//   "embedding": "s3://embedding/vector"
// }
//
// // Raw data -> Topic (for query)
// {
//   "PK": "RAW_DATA#12345",
//   "SK": "TOPIC#finance",
//   "confidence": 0.92,
//   "inference_timestamp": "2024-01-15T10:35:00Z"
// }
//
// // Topic -> Raw data (for query)
// {
//   "PK": "TOPIC#finance", 
//   "SK": "RAW_DATA#12345",
//   "confidence": 0.92,
//   "inference_timestamp": "2024-01-15T10:35:00Z"
// }

const QuickSaveTable = new Table({
	documentClient,
	partitionKey: {
		name: 'PK',
		type: 'string'
	},
	sortKey: {
		name: 'SK',
		type: 'string'
	},
	name: process.env.DYNAMODB_TABLE_NAME!
})

export const DataEntity = new Entity({
	name: 'DATA',
	table: QuickSaveTable,
	schema: item({
		dataId: string().key(),
		sourceDate: string(),
		body: string()
	}).and(prevSchema => ({
		PK: string().key().link<typeof prevSchema>(({ dataId }) => `DATA#${dataId}`),
		SK: string().key().link<typeof prevSchema>(({ dataId }) => `DATA#${dataId}`),
	}))
})

export const TopicEntity = new Entity({
	name: 'TOPIC',
	table: QuickSaveTable,
	schema: item({
		topicId: string().key(),
	}).and(prevSchema => ({
		PK: string().key().link<typeof prevSchema>(({ topicId }) => `TOPIC#${topicId}`),
		SK: string().key().link<typeof prevSchema>(({ topicId }) => `TOPIC#${topicId}`),
	}))
})

export const TopicToRawDataEntity = new Entity({
	name: 'TOPIC_TO_DATA',
	table: QuickSaveTable,
	schema: item({
		topicId: string().key(), // the actual topic e.g. "finance"
		dataId: string().key(),
		confidence: number(), // 0 to 1
		sentiment: number(), // -1, 0, 1
		inferenceTimestamp: string()
	}).and(prevSchema => ({
		PK: string().key().link<typeof prevSchema>(({ topicId }) => `TOPIC#${topicId}`),
		SK: string().key().link<typeof prevSchema>(({ dataId }) => `DATA#${dataId}`),
	}))
})

export const saveRedditDataDDB = async (dataProduced: RawDataProducedEvent) => {
	await DataEntity.build(PutItemCommand)
		.item({
			dataId: dataProduced.data.id,
			sourceDate: dataProduced.meta.source_date,
			body: dataProduced.data.body
		}).options({ returnValues: 'ALL_OLD' }).send()
}

// Persist a topic itself
export const saveTopic = async (topicId: string) => {
	await TopicEntity.build(PutItemCommand)
		.item({
			topicId
		}).options({ returnValues: 'ALL_OLD' }).send()
}

// Persist a relation TOPIC -> DATA
// as well as confidence and sentiment
export const saveTopicDataRelation = async (topicId: string, dataId: string, confidence: number, sentiment: number) => {
	await TopicToRawDataEntity.build(PutItemCommand)
		.item({
			topicId,
			dataId,
			confidence,
			sentiment,
			inferenceTimestamp: new Date().toISOString()
		}).options({ returnValues: 'ALL_OLD' }).send()
}

export const getDataByTopic = async (topicId: string) => {
	const r = await QuickSaveTable.build(QueryCommand)
		.entities(TopicToRawDataEntity)
		.query({ partition: `TOPIC#${topicId}` })
		.send()

	// Might have to actually store the opposite relation...
	return r.Items
}

export const getBodyByDataId = async (dataId: string) => {
	const r = await QuickSaveTable.build(QueryCommand)
		.entities(DataEntity)
		.query({ partition: `DATA#${dataId}` })
		.options({ limit: 1, attributes: ['body'] })
		.send()
	return r.Items?.[0]?.body
}
