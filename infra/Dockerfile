FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

WORKDIR /app
COPY pyproject.toml ./
COPY src ./src
COPY app ./app
COPY scripts ./scripts

# The demo is read-only at runtime. A numeric unprivileged UID avoids requiring
# an OS account while keeping the image dependency-free.
USER 65532:65532

EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/api/health', timeout=2).read()" || exit 1
CMD ["python", "scripts/run_demo.py", "--host", "0.0.0.0", "--port", "8080"]
