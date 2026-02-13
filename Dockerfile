FROM ghcr.io/astral-sh/uv:latest AS uv

FROM python:3.13-alpine
COPY --from=uv /uv /uvx /bin/
RUN apk add --no-cache gcc musl-dev linux-headers libffi-dev openssl-dev curl
WORKDIR /app

RUN addgroup -g 1000 -S appgroup && \
    adduser -u 1000 -S appuser -G appgroup -s /sbin/nologin

COPY --chown=root:root pyproject.toml uv.lock ./
RUN uv pip install --system .

COPY --chown=root:root . .
ENV PYTHONPATH=/app
USER appuser
