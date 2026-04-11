ARG BASE_IMAGE=ghcr.io/meta-pytorch/openenv-base:latest

# ---------------- BUILDER ----------------
FROM ${BASE_IMAGE} AS builder

WORKDIR /app

# Install uv directly without apt-get
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# Copy code
COPY . /app/env
WORKDIR /app/env

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=cache,target=/root/.cache/pip \
    uv sync --frozen && \
    . .venv/bin/activate && \
    pip install .

# ---------------- RUNTIME ----------------
FROM ${BASE_IMAGE}

WORKDIR /app

COPY --from=builder /app/env/.venv /app/.venv
COPY --from=builder /app/env /app/env
COPY --from=builder /app/env/openenv.yaml /app/openenv.yaml

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app/env:$PYTHONPATH"
ENV OPENENV_YAML_PATH=/app/openenv.yaml
ENV PORT=7860

EXPOSE 7860

CMD ["sh", "-c", "uvicorn incident_rca_env.server.app:app --host 0.0.0.0 --port ${PORT} --timeout-keep-alive 75"]

HEALTHCHECK CMD curl -f http://localhost:${PORT}/health || exit 1