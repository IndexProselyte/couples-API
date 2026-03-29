FROM python:3.12-slim

# Create a non-root user so the process doesn't run as root inside the container.
RUN addgroup --system app && adduser --system --ingroup app app

WORKDIR /app

# Install dependencies in a separate layer so rebuilds are fast when only
# application code changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code.
COPY . .

# Pre-create directories the app writes to and hand them to the app user.
# Both are overridden by named volumes in docker-compose, but having them here
# makes the image work standalone too.
RUN mkdir -p /data /app/uploads \
    && chown -R app:app /data /app/uploads /app

USER app

EXPOSE 8000

# --forwarded-allow-ips lets uvicorn trust the X-Forwarded-* headers that
# nginx injects, so request.client.host reflects the real client IP.
CMD ["uvicorn", "main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--forwarded-allow-ips", "*"]
