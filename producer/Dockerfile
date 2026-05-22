FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY producer_kafka.py .

CMD ["python", "-u", "producer_kafka.py"]