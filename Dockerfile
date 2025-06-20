# Use Python 3.11 slim image for smaller size
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=5000

# Install system dependencies including curl for health check
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies directly
RUN pip install --no-cache-dir \
    fastapi==0.104.1 \
    uvicorn==0.24.0 \
    sqlalchemy==2.0.23 \
    psycopg2-binary==2.9.9 \
    "pydantic[email]==2.5.0" \
    "python-jose[cryptography]==3.3.0" \
    "passlib[bcrypt]==1.7.4" \
    python-multipart==0.0.6 \
    requests==2.31.0 \
    pytest==7.4.3 \
    httpx==0.25.2 \
    email-validator==2.1.0

# Copy application code
COPY . .

# Create non-root user for security
RUN adduser --disabled-password --gecos '' jobapp
RUN chown -R jobapp:jobapp /app
USER jobapp

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Use uvicorn for FastAPI instead of python main.py
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5000"]