#!/usr/bin/env node
import * as cdk from 'aws-cdk-lib';
import { OceanStack } from '../lib/ocean-stack';
import { TrawlerStack } from '../lib/trawler-stack';
import { ReservoirStack } from '../lib/reservoir-stack';
import { MinervaStack } from '../lib/minerva-stack';

const app = new cdk.App();

const rootStack = new OceanStack(app, 'Ocean')
const vpc = rootStack.vpc;

const trawler = new TrawlerStack(app, 'Trawler', { vpc });

const reservoirStack = new ReservoirStack(app, 'Reservoir', { vpc });

reservoirStack.createFrontendHandler(
  '../reservoir',
  'data'
)

const rawDataSavedEvent = reservoirStack.persist_topic(
	trawler.dataTopic,
	'../reservoir/index.ts',
	'reservoir.raw',
)


const reservoirPyABSAQueue = reservoirStack.newPersistenceQueue(
	'../reservoir/pyabsa.ts',
	'PyABSA'
)

const reservoirEmbedQueue = reservoirStack.newPersistenceQueue(
	'../reservoir/embedding.ts',
	'reservoir.embed'
)

const minerva = new MinervaStack(app, 'Minerva', {
	vpc,
	dataSavedTopic: reservoirStack.snsTopic
})

minerva.createECSWorker(
	'PYABSA',
	rawDataSavedEvent,
	reservoirPyABSAQueue
)

minerva.createECSWorker(
	'EMBED',
	'reservoir.keyword',
	reservoirEmbedQueue
)
