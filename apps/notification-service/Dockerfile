FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app:/app/apps/notification-service

WORKDIR /app

COPY libs /app/libs
COPY apps/notification-service /app/apps/notification-service

WORKDIR /app/apps/notification-service
RUN pip install --no-cache-dir -e .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
