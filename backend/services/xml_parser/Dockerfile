FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY parser_app.py .

ENV PORT=5000
# WARNING: Change this token for production! This default is for development only.
ENV XML_PARSER_TOKEN=dev-token-12345

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "parser_app:app"]
