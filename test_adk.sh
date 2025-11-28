#!/bin/bash

# Script to test agents using ADK web interface
# Usage: ./test_adk.sh [port]

set -e

PORT=${1:-8009}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Utsava Sathi - ADK Testing${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

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
    echo -e "${YELLOW}Warning: .env file not found. Make sure GOOGLE_API_KEY is set.${NC}"
fi

# Check if ADK is installed
if ! command -v adk &> /dev/null; then
    echo -e "${YELLOW}ADK not found. Installing google-adk...${NC}"
    pip install google-adk
fi

echo ""
echo -e "${GREEN}Starting ADK web interface on port ${PORT}...${NC}"
echo ""
echo -e "${BLUE}Available Agents:${NC}"
echo "  1. ${GREEN}utsava_sathi_festival_planner${NC} (Single Agent - Legacy)"
echo "  2. ${GREEN}utsava_coordinator${NC} (Multi-Agent Coordinator)"
echo ""
echo -e "${BLUE}Specialized Agents (can be tested individually):${NC}"
echo "  3. ${GREEN}festival_research_agent${NC}"
echo "  4. ${GREEN}festival_preparation_agent${NC}"
echo "  5. ${GREEN}festival_experience_agent${NC}"
echo "  6. ${GREEN}festival_content_agent${NC}"
echo ""
echo -e "${YELLOW}ADK web interface will open in your browser.${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop.${NC}"
echo ""
echo -e "${BLUE}========================================${NC}"
echo ""

# Start ADK web
adk web --port "$PORT"

