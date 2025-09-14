import * as z from "zod"

const EventTypeEnumSchema = z.enum([
	"reservoir.raw",
	"reservoir.keyword",
	"trawl.raw",
]as const)

export type EventType = z.infer<typeof EventTypeEnumSchema>

const EventMetadataSchema = z.object({
   // INFO: Dont forget: this ID is what ties together all events
   // for a given source whether post,comment, reddit, web, etc...
  correlation_id: z.string(),
  event_type: EventTypeEnumSchema,
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
