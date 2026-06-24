FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app:/app/apps/payment-service

WORKDIR /app

COPY libs /app/libs
COPY apps/payment-service /app/apps/payment-service

WORKDIR /app/apps/payment-service
RUN pip install --no-cache-dir -e .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
