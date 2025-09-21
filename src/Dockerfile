# Dockerfile - backend (Flask + Gunicorn)
FROM python:3.11-slim

# Prevent Python writing .pyc and enable unbuffered logs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_VIRTUALENVS_CREATE=false

# Set working dir
WORKDIR /app

# Install OS deps required for some Python packages and runtime niceties
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       ca-certificates \
       curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install (keeps layers cacheable)
COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip \
    && pip install -r /app/requirements.txt

# Copy application code
COPY src /app/src
COPY gunicorn_conf.py /app/gunicorn_conf.py

# Create a non-root user and fix permissions
RUN groupadd -g 1000 appgroup \
    && useradd -u 1000 -g appgroup -m appuser \
    && chown -R appuser:appgroup /app

USER appuser
ENV PATH="/home/appuser/.local/bin:${PATH}"

# Expose listening port
EXPOSE 8000

# Healthcheck — simple HTTP probe for /health
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Entrypoint: gunicorn (use gunicorn_conf.py for post_fork warmup)
CMD ["gunicorn", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "2", \
     "--worker-class", "gthread", \
     "--threads", "8", \
     "--timeout", "120", \
     "--graceful-timeout", "30", \
     "--capture-output", \
     "--log-level", "info", \
     "--config", "/app/gunicorn_conf.py", \
     "src.app:app"]
