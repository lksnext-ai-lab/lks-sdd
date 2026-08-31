FROM python:3.13.15-slim@sha256:7ce4b6dfe35e55397b7cda544f8a13f191b7ae28dc5aad71fe664dbc9bc2623f
WORKDIR /app
RUN python -m pip install --no-cache-dir pip==26.2.1
COPY . .
RUN pip install --no-cache-dir --require-hashes -r requirements.lock
ENV PYTHONPATH=/app/src
CMD ["python", "-m", "uvicorn", "local_auth.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log", "--limit-concurrency", "32", "--timeout-keep-alive", "5"]
