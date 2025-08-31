#!/bin/bash

set -a
source ./ingestion/.env
set +a

set -e

# Validate required environment variables
echo "🔍 Checking required environment variables..."
REQUIRED_ENV_VARS=("REDDIT_CLIENT_ID" "REDDIT_SECRET" "REDDIT_REDIRECT_URI" "REDDIT_USER_AGENT")
MISSING_VARS=()

for var in "${REQUIRED_ENV_VARS[@]}"; do
    if [[ -z "$(eval echo \$$var)" ]]; then
        MISSING_VARS+=("$var")
    fi
done

if [[ ${#MISSING_VARS[@]} -gt 0 ]]; then
    echo "❌ Missing required environment variables:"
    printf '   - %s\n' "${MISSING_VARS[@]}"
    echo ""
    echo "Please set these environment variables before deploying:"
    echo "export REDDIT_CLIENT_ID=your_client_id"
    echo "export REDDIT_SECRET=your_secret"
    echo "export REDDIT_REDIRECT_URI=your_redirect_uri"
    echo "export REDDIT_USER_AGENT=your_user_agent"
    exit 1
fi

echo "✅ All required environment variables are set"

# Configuration
DOCKER_USERNAME="p5quared"
IMAGE_NAME="dorito_producer"
DOCKERFILE_PATH="ingestion"
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
docker build --platform linux/amd64 -t "${DOCKER_USERNAME}/${IMAGE_NAME}:${IMAGE_TAG}" -t "${DOCKER_USERNAME}/${IMAGE_NAME}:latest" .
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
