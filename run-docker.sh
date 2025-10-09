#!/bin/bash

# Fantasy NBA Advisor Docker Setup Script

echo "🏀 Fantasy NBA Advisor - Docker Setup"
echo "======================================"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ .env file not found. Please create one with your GROQ_API_KEY."
    exit 1
fi

# Check if GROQ_API_KEY is set
if ! grep -q "GROQ_API_KEY=" .env; then
    echo "❌ GROQ_API_KEY not found in .env file."
    exit 1
fi

echo "✅ Docker is running"
echo "✅ .env file found"

echo ""
echo "🚀 Building and starting Fantasy NBA Advisor..."
echo ""

# Build and start the services
docker-compose up --build -d

echo ""
echo "📊 Checking service status..."
echo ""

# Wait for services to be ready
sleep 10

# Check if services are running
if docker-compose ps | grep -q "Up"; then
    echo "✅ Services are running!"
    echo ""
    echo "🌐 Access the app at: http://localhost:8504"
    echo "📊 Qdrant dashboard at: http://localhost:6335/dashboard"
    echo ""
    echo "📱 To view logs:"
    echo "   docker-compose logs -f fantasy-nba"
    echo ""
    echo "🛑 To stop:"
    echo "   docker-compose down"
    echo ""
    echo "🗑️ To remove all data:"
    echo "   docker-compose down -v"
else
    echo "❌ Services failed to start. Check logs:"
    echo "   docker-compose logs"
fi