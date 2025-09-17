import { saveTopic, saveTopicDataRelation } from "./ddb";
import { eventHandler, MessageHandlerBuilder } from "./handling";
import { PyABSAProducedEvent, validatePyABSAProducedEvent } from "./parser";
import { publishKeyword } from "./publisher";
import { printMessage } from "./utils";

const savePyABSATopicDataRelation = async (e: PyABSAProducedEvent) => {
  await saveTopicDataRelation(e.data.keyword, e.meta.correlation_id, e.data.confidence, e.data.sentiment)
}

const PyABSARecordHandler = new MessageHandlerBuilder<PyABSAProducedEvent>()
	.withValidator(validatePyABSAProducedEvent)
	.withHandler(printMessage)
	.withHandler((e) => saveTopic(e.data.keyword))
	.withHandler(savePyABSATopicDataRelation)
	.withPublisher((e) => publishKeyword(e.data.keyword))
	.build()

const PyABSAEventHandler = eventHandler<PyABSAProducedEvent>(PyABSARecordHandler.handle.bind(PyABSARecordHandler))

export const handler = PyABSAEventHandler
