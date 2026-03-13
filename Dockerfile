FROM python:3.11-slim

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application code
COPY . .

# Create directories
RUN mkdir -p /app/reports /app/logs /tmp/rie_charts

# Expose port
EXPOSE ${PORT:-8050}

# Default command — runs the dashboard
CMD ["python", "-m", "engine.dashboard.server"]
