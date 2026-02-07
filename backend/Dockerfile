FROM python:3.11-slim

WORKDIR /app

# Install dependencies with optimizations for ARM/Raspberry Pi
COPY requirements.txt .
RUN pip install --no-cache-dir --compile -r requirements.txt \
    && find /usr/local -type d -name '__pycache__' -exec rm -rf {} + || true \
    && find /usr/local -type f -name '*.pyc' -delete

# Copy application
COPY app ./app
COPY sample_data.py .

# Create data directory
RUN mkdir -p /app/data

ENV SOLARAPP_DB_URL=sqlite:///./data/solarapp.db
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000

# Optimized for Raspberry Pi: single worker, reduced memory footprint
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--limit-concurrency", "50", "--timeout-keep-alive", "5"]
