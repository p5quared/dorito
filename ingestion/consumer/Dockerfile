FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

ADD . /app

WORKDIR /app

# Install only consumer and its dependencies
RUN uv sync --package consumer

CMD ["uv", "run", "--package", "consumer", "consumer"]