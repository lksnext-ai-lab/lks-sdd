FROM python:3.14.7-slim@sha256:ce40764625a4ff50df3548277632e7f96c4e77fe75fa848aae9885476e7df5a4
WORKDIR /app
RUN python -m pip install --no-cache-dir uv==0.12.5
COPY pyproject.toml uv.lock ./
COPY src ./src
RUN uv sync --frozen --no-dev
ENV PATH="/app/.venv/bin:$PATH"
USER 65532:65532
CMD ["python", "-m", "lks_sdd_worker.main"]
