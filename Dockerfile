FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml setup.py README.md ./
RUN pip install --no-cache-dir -e .

COPY src/ ./src/
COPY docs/ ./docs/

ENV PACTUM_HOST=0.0.0.0
ENV PACTUM_PORT=8000
ENV PACTUM_ENV=production

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

ENTRYPOINT ["pactum"]
CMD ["serve", "--host", "0.0.0.0", "--port", "8000"]
