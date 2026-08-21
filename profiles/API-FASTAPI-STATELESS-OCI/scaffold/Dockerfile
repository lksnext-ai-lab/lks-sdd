FROM python:3.14.7-slim@sha256:ce40764625a4ff50df3548277632e7f96c4e77fe75fa848aae9885476e7df5a4

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"
WORKDIR /app
RUN python -m pip install --no-cache-dir uv==0.12.5
COPY pyproject.toml uv.lock ./
COPY src ./src
RUN uv sync --frozen --no-dev
RUN useradd --create-home --uid 10001 appuser && chown -R appuser:appuser /app
USER 10001
EXPOSE 8000
CMD ["uvicorn", "lks_sdd_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
