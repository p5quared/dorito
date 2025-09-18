FROM python:3.13-slim

CMD ["uv", "run", "main.py"]

# Set working directory
WORKDIR /app

COPY ./checkpoints ./microsoft .

COPY pyproject.toml uv.lock ./

RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

RUN pip install uv

RUN uv export --no-dev --format requirements-txt > requirements.txt && \
    uv pip install --system --no-deps -r requirements.txt

RUN uv run spacy download en_core_web_sm

COPY *.py ./

