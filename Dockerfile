# Dockerfile

FROM python:3.10-slim

WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# Install database drivers if not in requirements.txt (we added them manually earlier)
RUN pip install --no-cache-dir sqlalchemy[asyncio] asyncpg alembic passlib[bcrypt] python-jose[cryptography]

# Copy project
COPY . .

# Run app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

