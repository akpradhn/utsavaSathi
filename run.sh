#!/bin/bash

# Script to run both the FastAPI backend and Streamlit frontend
# Usage: ./run.sh

set -e

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting Utsava Sathi services...${NC}"

# Check if virtual environment exists
if [ -d ".venv" ]; then
    echo -e "${YELLOW}Activating virtual environment...${NC}"
    source .venv/bin/activate
elif [ -d "venv" ]; then
    echo -e "${YELLOW}Activating virtual environment...${NC}"
    source venv/bin/activate
else
    echo -e "${YELLOW}No virtual environment found. Using system Python.${NC}"
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Warning: .env file not found. Make sure environment variables are set.${NC}"
fi

# Function to cleanup background processes on exit
cleanup() {
    echo -e "\n${YELLOW}Shutting down services...${NC}"
    if [ ! -z "$API_PID" ]; then
        kill $API_PID 2>/dev/null || true
        echo -e "${GREEN}API server stopped${NC}"
    fi
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup SIGINT SIGTERM EXIT

# Start FastAPI server in background
echo -e "${GREEN}Starting FastAPI server on port 8006...${NC}"
uvicorn ui.api:app --host 127.0.0.1 --port 8006 --reload &
API_PID=$!

# Wait a moment for the API to start
sleep 2

# Check if API started successfully
if ! kill -0 $API_PID 2>/dev/null; then
    echo -e "${RED}Failed to start API server${NC}"
    exit 1
fi

echo -e "${GREEN}API server started (PID: $API_PID)${NC}"

# Start Streamlit app (this will run in foreground)
echo -e "${GREEN}Starting Streamlit app...${NC}"
echo -e "${YELLOW}Streamlit will open in your browser. Press Ctrl+C to stop all services.${NC}"
streamlit run ui/app.py

