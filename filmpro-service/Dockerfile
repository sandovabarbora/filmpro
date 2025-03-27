FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install --no-cache-dir poetry==1.4.2

# Copy project dependency files
COPY pyproject.toml poetry.lock* /app/

# Configure poetry to not use a virtual environment
RUN poetry config virtualenvs.create false

# Install project dependencies
RUN poetry install --no-dev --no-interaction --no-ansi

# Install spaCy model
RUN python -m spacy download en_core_web_md

# Copy application code
COPY . /app/

# Create upload directory
RUN mkdir -p /app/uploads

# Set environment variables
ENV PYTHONPATH=/app \
    SCRIPT_UPLOAD_DIR=/app/uploads

# Expose port
EXPOSE 8000

# Start the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]