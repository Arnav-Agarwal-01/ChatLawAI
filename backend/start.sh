#!/bin/bash

echo "=================================================="
echo "LawMate AI - Legal Consultation Backend"
echo "=================================================="
echo ""

cd "$(dirname "$0")"

# Create venv if not exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate venv
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies (this may take a few minutes)..."
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "=================================================="
echo "Starting LawMate AI Backend Server..."
echo "=================================================="
echo ""
echo "Server will start on: http://localhost:8000"
echo "Press Ctrl+C to stop"
echo ""

# Run the app
python3 app.py
