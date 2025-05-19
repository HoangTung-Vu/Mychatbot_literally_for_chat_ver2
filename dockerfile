# syntax=docker/dockerfile:1

FROM python:3.12-alpine AS builder

WORKDIR /app

RUN apk add --no-cache --update \
    build-base \
    gcc \
    musl-dev \
    python3-dev
COPY requirements.txt .

RUN pip install --no-cache-dir --user -r requirements.txt
FROM python:3.12-alpine

WORKDIR /app

RUN apk add --no-cache --update \
    libstdc++ \
    && rm -rf /var/cache/apk/*

RUN addgroup --system app && \
    adduser --system --ingroup app app

COPY --from=builder /root/.local /home/app/.local
ENV PATH=/home/app/.local/bin:$PATH

COPY --chown=app:app . .

RUN mkdir -p /app/data/vector_store && \
    chown -R app:app /app/data

EXPOSE 8000

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app

RUN find /app -type f -name "*.py" -exec chmod 644 {} \; && \
    chmod 755 /app/run.py

USER app

CMD ["python", "run.py"]