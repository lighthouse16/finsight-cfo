FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (if any needed at runtime)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ app/

# Expose the backend port
EXPOSE 8000

# Run with uvicorn (no reload — production mode)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
