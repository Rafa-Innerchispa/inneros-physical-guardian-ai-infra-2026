FROM python:3.12-slim
WORKDIR /app
COPY src/ ./src/
ENV PYTHONPATH=/app/src HOST=127.0.0.1 PORT=8787 GUARDIAN_DB=/app/runtime/guardian.db
RUN useradd --create-home --uid 10001 guardian && mkdir -p /app/runtime && chown guardian:guardian /app/runtime
USER guardian
EXPOSE 8787
CMD ["python", "-m", "inneros_meta_guardian.web"]
