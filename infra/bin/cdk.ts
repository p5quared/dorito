#!/usr/bin/env node
import * as cdk from 'aws-cdk-lib';
import { DoritoStack } from '../lib/cdk-stack';

const app = new cdk.App();
const imageTag = app.node.tryGetContext('imageTag');
new DoritoStack(app, 'Dorito', { imageTag });
