# ──────────────────────────────────────────────────────────────────────────────
# Stage 1: Builder
# Install Python dependencies as a non-privileged --user install so the
# runtime stage never needs pip or build tools.
# ──────────────────────────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build

# Copy only the requirements file first to exploit Docker layer caching.
# The heavy pip-install layer is rebuilt only when requirements.txt changes.
COPY requirements.txt .

# Install into the current user's local directory (~root/.local in builder).
# --no-cache-dir keeps the layer small; build tools stay isolated here.
RUN pip install --no-cache-dir --user -r requirements.txt

# ──────────────────────────────────────────────────────────────────────────────
# Stage 2: Runtime
# Minimal image: no pip, no build tools, no root shell access.
# Security decisions are documented in DESIGN.md.
# ──────────────────────────────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

# Principle of Least Privilege: create a non-root system account with an
# explicit UID/GID of 1000 so Kubernetes runAsUser: 1000 matches exactly.
# -m creates the home directory; -s /sbin/nologin disallows interactive shells.
RUN groupadd -r -g 1000 appgroup && \
    useradd -r -u 1000 -g appgroup -m -d /home/appuser -s /sbin/nologin appuser

WORKDIR /app

# Copy only the installed packages from the builder — no pip or build artifacts.
COPY --from=builder --chown=appuser:appgroup /root/.local /home/appuser/.local

# Copy application source with correct ownership in a single layer.
COPY --chown=appuser:appgroup . .

# Drop privileges before the process starts.
USER appuser

# Inline comments are NOT valid inside a multi-line ENV instruction.
# Each ENV directive is kept on its own line to avoid build errors.
ENV PATH=/home/appuser/.local/bin:$PATH
ENV PORT=5000
# Prevent .pyc files from being written to disk (cleaner, smaller image).
ENV PYTHONDONTWRITEBYTECODE=1
# Ensure stdout/stderr are not buffered — required for log aggregators.
ENV PYTHONUNBUFFERED=1

EXPOSE 5000

# Docker-level health check (independent of Kubernetes probes).
# Provides health visibility when running with plain docker/docker-compose.
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')" || exit 1

# Use gunicorn as the production WSGI server.
# 2 workers handle concurrent requests without over-provisioning on a single core.
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "60", "main:app"]
