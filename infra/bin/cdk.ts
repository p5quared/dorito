#!/usr/bin/env node
import * as cdk from 'aws-cdk-lib';
import { DoritoStack } from '../lib/cdk-stack';
import { SaviorStack } from '../lib/savior-stack';



const app = new cdk.App();

// Persistence Service
const saviorStack = new SaviorStack(app, 'Savior');


// Data Producer Service
const imageTag = app.node.tryGetContext('imageTag');
new DoritoStack(app, 'Dorito', { 
	imageTag,
	saviorQueue: saviorStack.inputQueue 
});
