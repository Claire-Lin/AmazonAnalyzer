#!/bin/bash

# Amazon Product Analyzer - Local Development Runner

echo "🔍 Amazon Product Analyzer - Local Setup"
echo "========================================="

# Check if we're in the right directory
if [ ! -f "project_document.md" ]; then
    echo "❌ Please run this script from the AmazonAnalyzer root directory"
    exit 1
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found. Please ensure OPENAI_API_KEY is set"
    exit 1
fi

echo "✅ Environment file found"

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down services..."
    pkill -f "python main.py" 2>/dev/null || true
    pkill -f "uvicorn main:app" 2>/dev/null || true
    pkill -f "next dev" 2>/dev/null || true
    exit 0
}

# Set up trap to cleanup on Ctrl+C
trap cleanup INT

# Kill any existing processes
echo "🧹 Cleaning up existing processes..."
pkill -f "python main.py" 2>/dev/null || true
pkill -f "uvicorn main:app" 2>/dev/null || true
pkill -f "next dev" 2>/dev/null || true

sleep 2

# Check if Python dependencies are installed
echo "📦 Installing Python dependencies..."
cd backend
pip install -q fastapi uvicorn websockets pydantic sqlalchemy python-dotenv python-multipart requests playwright langchain langchain-openai langgraph langchain-core 2>/dev/null || echo "Some packages already installed"

# Install Playwright browsers
echo "🌐 Installing Playwright browsers..."
playwright install chromium 2>/dev/null || echo "Browsers already installed or failed to install"
cd ..

# Check if Node dependencies are installed
echo "📦 Installing Node dependencies..."
cd frontend
if [ ! -d "node_modules" ]; then
    npm install
else
    echo "Node modules already installed"
fi
cd ..

# Start backend
echo ""
echo "🚀 Starting Backend (FastAPI)..."
cd backend
nohup python main.py > ../backend.log 2>&1 &
BACKEND_PID=$!
cd ..

# Wait for backend to start
echo "⏳ Waiting for backend to start..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ Backend started successfully"
        break
    fi
    sleep 1
    if [ $i -eq 30 ]; then
        echo "❌ Backend failed to start after 30 seconds"
        echo "Check backend.log for errors"
        exit 1
    fi
done

# Start frontend
echo ""
echo "🎨 Starting Frontend (Next.js)..."
cd frontend
nohup npm run dev > ../frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

# Wait for frontend to start
echo "⏳ Waiting for frontend to start..."
sleep 5

# Check which port frontend is using
FRONTEND_PORT=$(grep -o "http://localhost:[0-9]*" frontend.log | head -1 | grep -o "[0-9]*$" || echo "3000")

echo ""
echo "🎉 System started successfully!"
echo "========================================="
echo "📱 Frontend: http://localhost:$FRONTEND_PORT"
echo "🔧 Backend:  http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "🧪 Test URL: https://www.amazon.com/Tamagotchi-Nano-Peanuts-Silicone-Case/dp/B0FB7FQWJL"
echo ""
echo "📋 Monitoring logs:"
echo "- Backend: tail -f backend.log"
echo "- Frontend: tail -f frontend.log"
echo ""
echo "🛑 Press Ctrl+C to stop all services"
echo ""

# Keep script running and show logs
tail -f backend.log frontend.log