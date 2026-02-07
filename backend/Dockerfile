FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY app ./app
COPY sample_data.py .

# Create data directory
RUN mkdir -p /app/data

ENV SOLARAPP_DB_URL=sqlite:///./data/solarapp.db

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
