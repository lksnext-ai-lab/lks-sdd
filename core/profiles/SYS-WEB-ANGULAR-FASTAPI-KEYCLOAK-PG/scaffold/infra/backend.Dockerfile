FROM python:3.14.7-slim@sha256:ce40764625a4ff50df3548277632e7f96c4e77fe75fa848aae9885476e7df5a4
WORKDIR /app
RUN python -m pip install --no-cache-dir uv==0.12.5
COPY apps/backend/pyproject.toml apps/backend/uv.lock ./
RUN uv sync --frozen --no-dev
COPY apps/backend/src ./src
ENV PATH="/app/.venv/bin:$PATH" PYTHONPATH="/app/src"
USER 65532:65532
EXPOSE 8000
CMD ["uvicorn", "lks_sdd_app.main:app", "--host", "0.0.0.0", "--port", "8000"]
