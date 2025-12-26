# Dockerfile pour Railway / Render
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements-mobile.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements-mobile.txt

# Copy app
COPY mobile_app.py .

# Create captures directory
RUN mkdir -p captures

# Expose port
EXPOSE 5000

# Run
CMD ["python", "mobile_app.py"]

