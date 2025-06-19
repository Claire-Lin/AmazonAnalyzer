#!/bin/bash

echo "🚀 Starting Amazon Product Analyzer System"
echo "=========================================="

# Kill any existing processes
echo "🧹 Cleaning up existing processes..."
pkill -f "python main.py" 2>/dev/null || true
pkill -f "uvicorn main:app" 2>/dev/null || true
pkill -f "next dev" 2>/dev/null || true

sleep 2

# Start backend
echo "🔧 Starting backend on port 8000..."
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
        exit 1
    fi
done

# Start frontend
echo "🎨 Starting frontend on port 3000..."
cd frontend
nohup npm run dev > ../frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

# Wait for frontend to start
echo "⏳ Waiting for frontend to start..."
sleep 5

echo ""
echo "🎉 System started successfully!"
echo "================================"
echo "📱 Frontend: http://localhost:3000 (or check logs for actual port)"
echo "🔧 Backend:  http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "🧪 Test URL: https://www.amazon.com/Tamagotchi-Nano-Peanuts-Silicone-Case/dp/B0FB7FQWJL"
echo ""
echo "📋 Logs:"
echo "Backend: tail -f backend.log"
echo "Frontend: tail -f frontend.log"
echo ""
echo "🛑 To stop: pkill -f 'python main.py' && pkill -f 'next dev'"