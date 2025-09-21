# Use the official AWS Lambda Node.js runtime as the base image
FROM public.ecr.aws/lambda/nodejs:20

# Copy package.json and package-lock.json
COPY package*.json ./

# Install dependencies
RUN npm ci

COPY tsconfig.json ./
COPY *.ts ./

RUN npm install typescript @types/node --no-save && \
    npx tsc && \
    npm uninstall typescript @types/node

# Set the CMD to your handler
CMD ["dist/similar_topics.handler"]
