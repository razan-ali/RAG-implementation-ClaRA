#!/bin/bash

# ClaRA RAG System - Startup Script

echo "Starting ClaRA RAG System..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo ""
    echo "⚠️  Please edit .env and add your API keys before running again!"
    echo ""
    exit 1
fi

# Install/update dependencies
echo "Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Create necessary directories
mkdir -p uploads vector_db static

# Run the application
echo ""
echo "✅ Starting server..."
echo "📍 Access the interface at: http://localhost:8000"
echo "📚 API documentation at: http://localhost:8000/docs"
echo ""

python main.py
