FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY src/ ./src/
COPY .env .env

# Create necessary directories
RUN mkdir -p data monitoring

# Expose the port that Streamlit runs on
EXPOSE 8501

# Default command (can be overridden by docker-compose)
CMD ["streamlit", "run", "src/app.py", "--server.address", "0.0.0.0", "--server.port", "8501"]