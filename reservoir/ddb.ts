import { DynamoDBClient } from "@aws-sdk/client-dynamodb";
import { DynamoDBDocumentClient } from "@aws-sdk/lib-dynamodb";
import { any, Entity, item, PutItemCommand, string, Table } from "dynamodb-toolbox";
import { RawDataProducedEvent } from "./parser";

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

export const RawDataEntity = new Entity({
  name: 'RAW_DATA',
  table: QuickSaveTable,
  schema: item({
	id: string().key(),
	sourceDate: string(),
	data: any()
  }).and(prevSchema => ({
	PK: string().key().link<typeof prevSchema>(({id}) => `RAW_DATA#${id}`),
	SK: string().key().link<typeof prevSchema>(({id}) => `RAW_DATA#${id}`),
  }))
})

export const saveRedditDataDDB = async (dataProduced: RawDataProducedEvent) => {
  await RawDataEntity.build(PutItemCommand)
  .item({
	id: dataProduced.data.id,
	sourceDate: dataProduced.meta.source_date,
	data: dataProduced.data
  }).options({ returnValues: 'ALL_OLD'}).send()
}
