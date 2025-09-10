FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    make \
    curl \
    docker.io \
    xvfb \
    x11vnc \
    scrot \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy devix files
COPY . /app/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create logs directory
RUN mkdir -p /app/logs

# Set Python path
ENV PYTHONPATH=/workspace:/app

# Entry point
CMD ["python", "supervisor.py"]
