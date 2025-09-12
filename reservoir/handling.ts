import { SQSBatchItemFailure, SQSBatchResponse, SQSEvent, SQSRecord } from "aws-lambda";

export class MessageHandlerBuilder<I> {
	private storageHandlers: Array<(input: I) => Promise<void>> = [];
	private validator!: (input: any) => input is I;
	private publisher!: (input: I) => Promise<void>;

	withValidator(validator: (input: any) => input is I) {
		this.validator = validator;
		return this;
	}

	withHandler(handler: (input: I) => Promise<void>) {
		this.storageHandlers.push(handler);
		return this;
	}

	withPublisher(publisher: (input: I) => Promise<void>) {
		this.publisher = publisher;
		return this;
	}

	build(): MessageHandler<I> {
		if (!this.validator) {
			throw new Error("Parser is required");
		}

		if (!this.publisher) {
			throw new Error("Publisher is required");
		}
		return new MessageHandler(this.validator, this.storageHandlers, this.publisher);
	}
}


class MessageHandler<I> {
	constructor(
		protected validator: (input: any) => input is I,
		protected storage_handlers: Array<(input: I) => Promise<void>>,
		protected publish: (input: I) => Promise<void>
	) { }

	async handle(input: I) {
		this.validator(input)
		await Promise.all(this.storage_handlers.map(h => h(input)))
		await this.publish(input)
	}
}

export type Handler<T> = (input: T) => Promise<void>
export const eventHandler = <T>(h: Handler<T>) => async (event: SQSEvent): Promise<SQSBatchResponse> => {
	console.log(`Received ${event.Records.length} records`);

	const batchItemFailures: SQSBatchItemFailure[] = [];

	await Promise.all(event.Records.map(async (record) => {
		try {
			const message = JSON.parse(record.body);
			await h(message)
		} catch (error) {
			console.error(`Failed to process message ${record.messageId}:`, error);
			console.error(`Offending message body: ${record.body}`);
			batchItemFailures.push({
				itemIdentifier: record.messageId
			});
		}
	}))

	console.log(`Batch processing completed with ${batchItemFailures.length} failures`);

	return {
		batchItemFailures
	};
}
