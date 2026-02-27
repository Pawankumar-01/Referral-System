FROM python:3.11-slim

# Neutral work directory
WORKDIR /usr/src/app

# Install system dependencies for PostgreSQL
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the code
COPY . .

# Set the environment variable for Fly.io
ENV PORT=8080

# Use the full path for gunicorn or call it via python -m to be safe
CMD ["python", "-m", "gunicorn", "-k", "uvicorn.workers.UvicornWorker", "app.main:app", "--bind", "0.0.0.0:8080", "--timeout", "90"]