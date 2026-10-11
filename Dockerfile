# Tutor Portal — container image for hosts that build from a Dockerfile
# (Railway, Render, Fly, or a VPS). The app serves both the API and the SPA.
FROM python:3.12-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ backend/
COPY static/ static/
RUN mkdir -p /app/data

EXPOSE 8080
# PORT is provided by the platform; data/ is expected to be a mounted volume so
# the SQLite database survives redeploys.
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
