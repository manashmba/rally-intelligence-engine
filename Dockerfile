FROM python:3.11-slim

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements-railway.txt .
RUN pip install --no-cache-dir -r requirements-railway.txt

# Application code
COPY . .

# Create directories
RUN mkdir -p /app/reports /app/logs /tmp/rie_charts

# Default command
ENV PYTHONPATH=/app
CMD ["python", "engine/dashboard/server.py"]
