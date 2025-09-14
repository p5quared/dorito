FROM python:3.13-slim

RUN pip install uv

# Set working directory
WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN uv export --no-dev --format requirements-txt > requirements.txt && \
    uv pip install --system --no-deps -r requirements.txt

COPY *.py ./

CMD ["uv", "run", "main.py"]
