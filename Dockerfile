FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    ACQUISITION_DATA_DIR=/data

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl gcc libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.9.5 /uv /uvx /bin/
COPY pyproject.toml README.md LICENCE.md LEGAL_NOTICE.md ./
COPY openoutreach ./openoutreach
COPY webapp ./webapp
COPY web_manage.py ./

RUN uv pip install --system . gunicorn "whitenoise>=6.8,<7" "boto3>=1.35,<2"

COPY deploy/container-entrypoint.sh /usr/local/bin/container-entrypoint
RUN chmod +x /usr/local/bin/container-entrypoint && mkdir -p /data /app/staticfiles

EXPOSE 8080
CMD ["/usr/local/bin/container-entrypoint"]
