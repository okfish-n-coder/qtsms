# Dockerfile for running QTSMS client tests and examples
# 
# Build: docker build -t qtsms-client .
# Run tests (default): docker run --rm qtsms-client
# Run example: docker run --rm qtsms-client python examples/send_sms.py --help
# Send SMS: docker run --rm qtsms-client python examples/send_sms.py --api-key KEY --phone +79991234567 --text "Hello"
FROM python:3.12-slim

WORKDIR /app

# Install curl first to pull in all necessary SSL/TLS libraries and configurations
# python:slim images sometimes lack proper SSL setup that curl brings automatically
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && update-ca-certificates

# Copy project files
COPY qtsms_client/ /app/
COPY examples/ /app/examples/
COPY tests/ /app/tests/
COPY pyproject.toml /app/

# Install the package and dev dependencies (includes pytest, pytest-asyncio, pydantic)
RUN pip install --no-cache-dir ".[dev]"

# Default command: run tests
# Override with: docker run --rm qtsms-client python examples/send_sms.py [args]
CMD ["pytest", "/app/tests/", "-v", "--tb=short"]
