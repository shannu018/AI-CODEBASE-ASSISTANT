FROM python:3.11-slim

# Install system dependencies needed by chromadb and onnxruntime
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app
COPY . .

# Create required directories
RUN mkdir -p uploads chroma_db

# Expose the port Railway will assign
EXPOSE 8080

# Start the app with gunicorn
CMD gunicorn app:app --bind 0.0.0.0:${PORT:-8080} --workers 2 --timeout 120
