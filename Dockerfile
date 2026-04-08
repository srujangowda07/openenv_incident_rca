FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
	PYTHONUNBUFFERED=1 \
	UV_LINK_MODE=copy

WORKDIR /app

RUN apt-get update && \
	apt-get install -y --no-install-recommends curl ca-certificates && \
	rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

# Copy dependency metadata first for better build caching
COPY pyproject.toml README.md openenv.yaml /app/
COPY uv.lock /app/uv.lock

RUN if [ -f uv.lock ]; then \
		uv sync --frozen --no-dev; \
	else \
		uv sync --no-dev; \
	fi

# Copy full source after dependencies
COPY . /app

RUN if [ -f uv.lock ]; then \
		uv sync --frozen --no-dev; \
	else \
		uv sync --no-dev; \
	fi

ENV PATH="/app/.venv/bin:$PATH" \
	PYTHONPATH="/app:$PYTHONPATH" \
	PORT=8000

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
	CMD curl -f http://127.0.0.1:${PORT}/health || exit 1

CMD ["sh", "-c", "uv run uvicorn server.app:app --host 0.0.0.0 --port ${PORT}"]