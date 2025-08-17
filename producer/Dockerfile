FROM ghcr.io/astral-sh/uv:python3.13-alpine

ADD . /app

WORKDIR /app

RUN uv sync --locked

# Presuming there is a `my_app` command provided by the project
CMD ["uv", "run", "main.py"]
