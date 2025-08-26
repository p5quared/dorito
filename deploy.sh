#!/bin/bash

set -e

# Configuration
DOCKER_USERNAME="p5quared"
IMAGE_NAME="dorito_producer"
DOCKERFILE_PATH="data_source"
CDK_APP_PATH="infra"

# Generate timestamp-based tag
TIMESTAMP=$(date +"%Y%m%d-%H%M%S")
GIT_HASH=$(git rev-parse --short HEAD)
IMAGE_TAG="${TIMESTAMP}-${GIT_HASH}"

echo "🚀 Starting deployment process..."
echo "Image tag: ${IMAGE_TAG}"

# Step 1: Build Docker image
echo "📦 Building Docker image..."
cd "${DOCKERFILE_PATH}"
docker build -t "${DOCKER_USERNAME}/${IMAGE_NAME}:${IMAGE_TAG}" -t "${DOCKER_USERNAME}/${IMAGE_NAME}:latest" .
cd ..

# Step 2: Push to Docker Hub
echo "🔄 Pushing image to Docker Hub..."
docker push "${DOCKER_USERNAME}/${IMAGE_NAME}:${IMAGE_TAG}"
docker push "${DOCKER_USERNAME}/${IMAGE_NAME}:latest"

# Step 3: Deploy with CDK
echo "☁️  Deploying to AWS with CDK..."
cd "${CDK_APP_PATH}"
npm run build
cdk deploy --all --context imageTag="${IMAGE_TAG}" --require-approval never

echo "✅ Deployment completed successfully!"
echo "Image: ${DOCKER_USERNAME}/${IMAGE_NAME}:${IMAGE_TAG}"
