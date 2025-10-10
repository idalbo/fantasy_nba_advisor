.PHONY: help ingest-data project-run stop clean build

help:
	@echo "Available commands:"
	@echo "  ingest-data  - Download and ingest data into the vector database"
	@echo "  project-run  - Start the application with Docker Compose"
	@echo "  stop         - Stop all running containers"
	@echo "  clean        - Remove all containers and volumes"
	@echo "  build        - Build the Docker images"

build:
	@echo "Building Docker images..."
	docker-compose build

ingest-data: build
	@echo "Starting Qdrant service..."
	docker-compose up -d qdrant
	@echo "Waiting for Qdrant to be ready..."
	sleep 20
	@echo "Running data ingestion..."
	docker-compose run --rm fantasy-nba python -c "import sys; sys.path.append('src'); from data_ingestion import DataIngestion; DataIngestion().run_ingestion()"
	@echo "Data ingestion completed!"

project-run: build
	@echo "Starting the Fantasy NBA Advisor application..."
	docker-compose up -d

stop:
	@echo "Stopping all services..."
	docker-compose down

clean:
	@echo "Cleaning up containers and volumes..."
	docker-compose down -v
	docker system prune -f