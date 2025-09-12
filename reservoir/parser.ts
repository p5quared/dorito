import * as z from "zod"

const EventTypeEnumSchema = z.enum([
	"reservoir.raw",
	"trawl.raw",
]as const)

export type EventType = z.infer<typeof EventTypeEnumSchema>

const EventMetadataSchema = z.object({
  correlation_id: z.string(),
  event_type: EventTypeEnumSchema,
  source_date: z.string()
})

export type EventMetadata = z.infer<typeof EventMetadataSchema>

const RawDataSchema = z.object({
	id: z.string(), // Identifier that is unique to the body/data/source
	body: z.string()
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
