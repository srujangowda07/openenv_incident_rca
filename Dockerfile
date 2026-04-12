FROM ghcr.io/meta-pytorch/openenv-base:latest

WORKDIR /app

COPY . /app/env
COPY openenv.yaml /app/openenv.yaml

WORKDIR /app/env

RUN pip install -e . --quiet

ENV PATH="/app/env/.venv/bin:$PATH"
ENV PYTHONPATH="/app/env:$PYTHONPATH"
ENV OPENENV_YAML_PATH=/app/openenv.yaml
ENV PORT=7860

EXPOSE 7860

CMD ["sh", "-c", "uvicorn server.app:app --host 0.0.0.0 --port ${PORT}"]

HEALTHCHECK CMD curl -f http://localhost:${PORT}/health || exit 1