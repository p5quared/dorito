FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

ADD . /app

WORKDIR /app

# Accept build argument to specify which service to install
ARG SERVICE=producer

# Install only the specified service and its dependencies
RUN uv sync --package ${SERVICE}

# Default command can be overridden at runtime
CMD uv run --package ${SERVICE} ${SERVICE}
