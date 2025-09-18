import * as z from "zod"

// TODO: Event type should be configured at the CDK level
// We define the events that this handler will emit, 
// because every handler handles one type of message, they will
// only ever need to emit one type of event
// const EventTypeEnumSchema = z.enum([
// 	"reservoir.raw",
// 	"reservoir.keyword",
// 	"trawl.raw",
// ] as const)

// export type EventType = z.infer<typeof EventTypeEnumSchema>

const EventMetadataSchema = z.object({
	correlation_id: z.string(),
	source_date: z.string()
})

export type EventMetadata = z.infer<typeof EventMetadataSchema>

const RawDataSchema = z.object({
	id: z.string(),
	body: z.string()
})

const KeyWordSchema = z.object({
	keyword: z.string(),
	confidence: z.number().min(0).max(1)
})

const RawDataProducedEnvelopeSchema = z.object({
	meta: EventMetadataSchema,
	data: RawDataSchema
})

export type RawDataProducedEvent = z.infer<typeof RawDataProducedEnvelopeSchema>

export const validateRawDataProducedEvent = (a: any): a is RawDataProducedEvent => {
	RawDataProducedEnvelopeSchema.parse(a)
	return true
}

const KeywordProducedEnvelopeSchema = z.object({
	meta: EventMetadataSchema,
	data: KeyWordSchema
})
export type KeywordProducedEvent = z.infer<typeof KeywordProducedEnvelopeSchema>

export const validateKeywordProducedEvent = (a: any): a is KeywordProducedEvent => {
	KeywordProducedEnvelopeSchema.parse(a)
	return true
}

const PyABSASchema = z.object({
	keyword: z.string(),
	sentiment: z.int(),
	confidence: z.number().min(0).max(1)
})

const PyABSAProducedEnvelopeSchema = z.object({
	meta: EventMetadataSchema,
	data: PyABSASchema
})

export type PyABSAProducedEvent = z.infer<typeof PyABSAProducedEnvelopeSchema>

export const validatePyABSAProducedEvent = (a: any): a is PyABSAProducedEvent => {
	PyABSAProducedEnvelopeSchema.parse(a)
	return true
}

const EmbeddingSchema = z.object({
  keyword: z.string(),
  vector: z.array(z.number()),
  dimension: z.number().int().positive()
})

const EmbeddingProducedEnvelopeSchema = z.object({
  meta: EventMetadataSchema,
  	data: EmbeddingSchema
  })

export type EmbeddingProducedEvent = z.infer<typeof EmbeddingProducedEnvelopeSchema>

export const validateEmbeddingProducedEvent = (a: any): a is EmbeddingProducedEvent => {
  EmbeddingProducedEnvelopeSchema.parse(a)
  	return true
}
