FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

ADD . /app

WORKDIR /app

# Install only producer and its dependencies
RUN uv sync --package producer

CMD ["uv", "run", "--package", "producer", "producer"]