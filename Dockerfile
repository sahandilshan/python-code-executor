# Use Python 3.12 slim image for smaller size
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml README.md ./
COPY python_code_executor/ ./python_code_executor/

# Install the package
RUN pip install --no-cache-dir -e .

# Create a non-root user for security
RUN useradd --create-home --shell /bin/bash executor

# Create the sandbox venv DURING BUILD (as root, then chown)
RUN python -m venv /home/executor/.python_executor_sandbox && \
    chown -R executor:executor /home/executor

# Switch to non-root user
USER executor

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV HOME=/home/executor

# Expose the SSE port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/sse || exit 1

# Run the MCP server with SSE transport
CMD ["python", "-m", "python_code_executor.server", "--sse", "--host", "0.0.0.0", "--port", "8000"]
