FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app:/app/apps/user-service

WORKDIR /app

COPY libs /app/libs
COPY apps/user-service /app/apps/user-service

WORKDIR /app/apps/user-service
RUN pip install --no-cache-dir -e .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
