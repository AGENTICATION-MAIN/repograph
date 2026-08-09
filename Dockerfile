FROM python:3.12-slim

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency specifications
COPY pyproject.toml setup.py README.md ./

# Install python dependencies
RUN pip install --no-cache-dir -e .

# Copy source code and docs
COPY src/ ./src/
COPY docs/ ./docs/

# Environment defaults
ENV AEGIS_HOST=0.0.0.0
ENV AEGIS_PORT=8000
ENV AEGIS_ENV=production
ENV AEGIS_LOG_LEVEL=INFO

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

ENTRYPOINT ["aegis"]
CMD ["serve", "--host", "0.0.0.0", "--port", "8000"]
