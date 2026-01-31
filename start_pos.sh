#!/bin/bash
# Start all services for the BlueOlive POS system

echo "========================================"
echo "BlueOlive POS - Multi-Service Startup"
echo "========================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print status
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Check if Python is installed
if ! command -v python &> /dev/null; then
    print_error "Python is not installed"
    exit 1
fi
print_status "Python found"

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    print_error "Node.js is not installed"
    exit 1
fi
print_status "Node.js found"

# Start POS FastAPI in background
echo ""
echo "Starting FastAPI POS System (Port 8001)..."
cd backend/pos
if [ ! -d "venv" ]; then
    print_warning "Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
source venv/bin/activate || . venv/Scripts/activate

# Install dependencies
pip install -q -r requirements.txt 2>/dev/null

# Start FastAPI
uvicorn main:app --host 127.0.0.1 --port 8001 &
POS_PID=$!
print_status "FastAPI POS started (PID: $POS_PID)"
cd ../..

echo ""
echo "Service Status:"
echo "  - FastAPI POS: http://localhost:8001"
echo "  - Django Backend: http://localhost:8000"
echo "  - Next.js Frontend: http://localhost:3000"
echo ""
echo "Documentation:"
echo "  - POS API Docs: http://localhost:8001/docs"
echo "  - Django Admin: http://localhost:8000/admin"
echo ""
echo "To stop all services, press Ctrl+C"
echo ""

# Wait for all background processes
wait

print_status "All services stopped"
