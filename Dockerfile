# Dockerfile for running QTSMS client tests and examples
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY qtsms_client/ /app/
COPY examples/ /app/examples/

# Install the package and dev dependencies
RUN pip install --no-cache-dir ".[dev]"

# Default command: run tests
# To run the example: docker run --rm qtsms-client python examples/send_sms.py --help
# Or: docker run --rm qtsms-client python examples/send_sms.py --api-key KEY --phone +79991234567 --text "Hello"
CMD ["pytest", "/app/tests/", "-v", "--tb=short"]
