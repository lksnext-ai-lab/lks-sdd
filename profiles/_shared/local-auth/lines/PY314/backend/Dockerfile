FROM python:3.14.7-slim@sha256:ce40764625a4ff50df3548277632e7f96c4e77fe75fa848aae9885476e7df5a4
WORKDIR /app
RUN python -m pip install --no-cache-dir pip==26.2.1
COPY . .
RUN pip install --no-cache-dir uv==0.12.5 && uv sync --frozen --no-install-project
ENV PYTHONPATH=/app/src
ENV PATH=/app/.venv/bin:$PATH
CMD ["python", "-m", "uvicorn", "local_auth.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log", "--limit-concurrency", "32", "--timeout-keep-alive", "5"]
