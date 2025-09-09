#!/usr/bin/env node
import * as cdk from 'aws-cdk-lib';
import { OceanStack } from '../lib/ocean-stack';
import { TrawlerStack } from '../lib/trawler-stack';
import { ReservoirStack } from '../lib/reservoir-stack';



const app = new cdk.App();

const rootStack = new OceanStack(app, 'Ocean', {})
const vpc = rootStack.vpc;

// Data Tap - Data Source
const trawler = new TrawlerStack(app, 'Trawler', 
  { vpc }
);

// Data Savior - Data Sink
const reservoirStack = new ReservoirStack(app, 'Reservoir',
	{ vpc }
);

reservoirStack.save_topic(
  trawler.dataTopic, 
  '../savior/index.ts',
  'RedditData',
  undefined
)
