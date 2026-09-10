FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

WORKDIR /app
COPY pyproject.toml ./
COPY src ./src
COPY app ./app
COPY scripts ./scripts

EXPOSE 8080
CMD ["python", "scripts/run_demo.py", "--host", "0.0.0.0", "--port", "8080"]
