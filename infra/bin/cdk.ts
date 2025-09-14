#!/usr/bin/env node
import * as cdk from 'aws-cdk-lib';
import { OceanStack } from '../lib/ocean-stack';
import { TrawlerStack } from '../lib/trawler-stack';
import { ReservoirStack } from '../lib/reservoir-stack';
import { MinervaStack } from '../lib/minerva-stack';



const app = new cdk.App();

const rootStack = new OceanStack(app, 'Ocean')
const vpc = rootStack.vpc;

// Data Tap - Data Source
const trawler = new TrawlerStack(app, 'Trawler', { vpc });

// Data Reservoir - Data Sink
const reservoirStack = new ReservoirStack(app, 'Reservoir', { vpc });

const rawDataSavedEvent = reservoirStack.persist_topic(
	trawler.dataTopic,
	'../reservoir/index.ts',
	'reservoir.raw',
)

const keyword_saver = reservoirStack.newPersistenceQueue(
  '../reservoir/keyword.ts',
  'Keyword'
)

const minerva = new MinervaStack(app, 'Minerva', { 
  vpc,
  dataSavedTopic: reservoirStack.snsTopic
})

minerva.createECSWorker(
  'KEYWORD', 
  rawDataSavedEvent,
  keyword_saver
)

