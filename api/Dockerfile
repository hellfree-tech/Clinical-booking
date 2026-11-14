FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PORT=8000 DB_PATH=/data/clinic.db
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
RUN useradd --create-home appuser && mkdir -p /data /app/data && chown appuser /data /app/data
USER appuser
EXPOSE 8000
# One worker: the in-memory rate limiter and per-request atomicity assume a single process.
CMD ["python", "-m", "app.server"]
