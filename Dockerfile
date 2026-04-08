FROM python:3.10-slim

RUN pip install uv

WORKDIR /app

COPY . /app

RUN uv sync


ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app:$PYTHONPATH"

CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "7860"]