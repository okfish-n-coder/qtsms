# Dockerfile for running QTSMS client tests and examples
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates openssl curl \
    && rm -rf /var/lib/apt/lists/* && update-ca-certificates

ENV SSL_CERT_DIR=/etc/ssl/certs/

# Copy project files
COPY qtsms_client/ /app/
COPY examples/ /app/examples/

# Install the package and dev dependencies
RUN pip install -U pip
RUN pip install -e ".[dev]"

RUN pip list

# Default command: run tests
# To run the example in editable mode:
#  docker run  -v "${PWD}/examples:/app/examples"  -v "${PWD}/qtsms_client:/app/" --rm qtsms-client python examples/send_sms.py --help
# Or: docker run   -v "${PWD}/examples:/app/examples" -v "${PWD}/qtsms_client:/app/"--rm qtsms-client python examples/send_sms.py --api-key KEY --phone +79991234567 --text "Hello"
CMD ["pytest", "/app/tests/", "-v", "--tb=short"]
