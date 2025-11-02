FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ src/
COPY config/ config/

# Create data and logs directories
RUN mkdir -p data logs

# Set Python path
ENV PYTHONPATH=/app/src

# Default command
CMD ["python", "-m", "src.main"]
