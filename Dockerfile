# Dockerfile for running QTSMS client tests
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY qtsms_client/ /app/

# Install the package and dev dependencies
RUN pip install --no-cache-dir ".[dev]"

# Run tests by default
CMD ["pytest", "tests/", "-v", "--tb=short"]
