FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml setup.py README.md ./
RUN pip install --no-cache-dir -e .

COPY src/ ./src/
COPY docs/ ./docs/

ENTRYPOINT ["repograph"]
CMD ["scan", "."]
