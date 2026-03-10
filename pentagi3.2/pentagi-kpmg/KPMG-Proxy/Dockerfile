FROM python:3.11-slim

LABEL maintainer="KPMG PentAGI Team"
LABEL description="KPMG Azure API Headers Injector for PentAGI"
LABEL version="2.0.0"

# Set working directory
WORKDIR /app

# Set proxy build args (pass from docker-compose)
ARG HTTP_PROXY
ARG HTTPS_PROXY
ENV http_proxy=$HTTP_PROXY
ENV https_proxy=$HTTPS_PROXY

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Configure pip to use trusted hosts
RUN pip config set global.trusted-host "pypi.org" \
    && pip config set global.trusted-host "files.pythonhosted.org" \
    && pip install --no-cache-dir -r requirements.txt --timeout 120

# Copy application code
COPY proxy_server.py .

# Create non-root user for security
RUN useradd -m -u 1000 injector && \
    chown -R injector:injector /app

# Switch to non-root user
USER injector

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Run the application
CMD ["python", "proxy_server.py"]
