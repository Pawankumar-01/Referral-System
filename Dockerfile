FROM python:3.11-slim

# Use a neutral path to avoid "app/app" confusion
WORKDIR /usr/src/app

# Install system dependencies for psycopg2/Postgres
RUN apt-get update && apt-get install -y libpq-dev gcc && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all files from your local referral_system folder
COPY . .

# Match the Fly.io default internal port
ENV PORT=8080

# Using gunicorn with uvicorn workers for production stability
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "app.main:app", "--bind", "0.0.0.0:8080", "--timeout", "90"]