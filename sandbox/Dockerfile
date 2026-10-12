FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        git \
        curl \
        bash \
        nodejs \
        npm \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 1000 --shell /bin/bash agent

COPY pyproject.toml README.md ./
COPY agent ./agent
COPY examples ./examples

RUN pip install --upgrade pip \
    && pip install .

COPY sandbox/entrypoint.sh /entrypoint.sh
RUN sed -i 's/\r$//' /entrypoint.sh && chmod +x /entrypoint.sh

RUN mkdir -p /ingest /workspace/scripts \
    && chown -R agent:agent /ingest /workspace /app

USER agent

ENV INGEST_PATH=/ingest \
    WORKSPACE_PATH=/workspace

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
    CMD curl -fsS http://127.0.0.1:8080/health || exit 1

ENTRYPOINT ["/entrypoint.sh"]
