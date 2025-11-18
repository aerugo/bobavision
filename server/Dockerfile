# Multi-stage Dockerfile for bobavision server with mpv
# ADR-007: Server Containerization with mpv for dependency isolation

# Stage 1: Builder - Install dependencies
FROM python:3.11-slim as builder

# Install system dependencies needed for Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install Python dependencies
WORKDIR /build
COPY pyproject.toml ./
COPY src/ ./src/

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -e .


# Stage 2: Runtime - Minimal production image
FROM python:3.11-slim

# Install mpv and runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    mpv \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set working directory
WORKDIR /app/server

# Copy application code
COPY src/ ./src/
COPY pyproject.toml ./

# Create directories for data persistence
RUN mkdir -p /app/data /app/media/library

# Environment variables
ENV PYTHONPATH=/app/server \
    PYTHONUNBUFFERED=1 \
    DATABASE_URL=/app/data/bobavision.db \
    MEDIA_DIRECTORY=/app/media/library

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/', timeout=5.0)" || exit 1

# Run server
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
