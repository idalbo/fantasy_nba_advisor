FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker layer caching
COPY requirements_docker.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements_docker.txt

# Copy the application code
COPY src/ ./src/
COPY streamlit_app.py .
COPY nba_players_full.json .
COPY .env .env

# Create necessary directories
RUN mkdir -p data monitoring evaluation

# Expose the port that Streamlit runs on
EXPOSE 8501

# Default command (can be overridden by docker-compose)
CMD ["streamlit", "run", "streamlit_app.py", "--server.address", "0.0.0.0", "--server.port", "8501"]