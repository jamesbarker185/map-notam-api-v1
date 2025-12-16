FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Default command, can be overridden by docker-compose
CMD ["python", "-m", "app.live_ingest"]
