ARG BASE_IMAGE=ghcr.io/meta-pytorch/openenv-base:latest

# ---------------- BUILDER ----------------
FROM ${BASE_IMAGE} AS builder

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends git curl && \
    rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh && \
    mv /root/.local/bin/uv /usr/local/bin/uv && \
    mv /root/.local/bin/uvx /usr/local/bin/uvx

# Copy code
COPY . /app/env
WORKDIR /app/env

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen

# ---------------- RUNTIME ----------------
FROM ${BASE_IMAGE}

WORKDIR /app

# ✅ COPY VENV (CRITICAL)
COPY --from=builder /app/env/.venv /app/.venv

# Copy code
COPY --from=builder /app/env /app/env

# Copy YAML
COPY --from=builder /app/env/openenv.yaml /app/openenv.yaml

# ✅ Use venv python
ENV PATH="/app/.venv/bin:$PATH"

# (optional but safe)
ENV PYTHONPATH="/app/env:$PYTHONPATH"

EXPOSE 7860
ENV PORT=7860

CMD ["sh", "-c", "uvicorn incident_rca_env.server.app:app --host 0.0.0.0 --port ${PORT}"]

HEALTHCHECK CMD curl -f http://localhost:${PORT}/health || exit 1