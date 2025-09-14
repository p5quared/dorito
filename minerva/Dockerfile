FROM python:3.13-slim

# Install uv
RUN pip install uv

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies to the system python
RUN uv export --no-dev --format requirements-txt > requirements.txt && \
    uv pip install --system --no-deps -r requirements.txt

# Copy source code
COPY src/ ./src/

# Install the package in development mode
RUN uv pip install --system -e .

# Set the CMD to run the ECS handler
CMD ["python", "-c", "from minerva.main import ecs_handler; ecs_handler()"]
