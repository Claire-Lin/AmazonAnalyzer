"""
Amazon Product Analysis System - FastAPI Backend

This is the main FastAPI application that provides REST API endpoints
for the Amazon product analysis system with multi-agent workflow.
"""

import os
import uuid
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from contextlib import asynccontextmanager

# Import our agents
from agents.supervisor import analyze_product
from services.websocket_manager import websocket_manager
from models.database import init_db
from models.analysis import AnalysisRequest, AnalysisResponse, AnalysisStatus


# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Starting Amazon Product Analysis System...")
    
    # Initialize database
    await init_db()
    
    # Initialize WebSocket manager
    websocket_manager.initialize()
    
    print("✅ System initialized successfully!")
    
    yield
    
    # Shutdown
    print("🔄 Shutting down Amazon Product Analysis System...")
    await websocket_manager.cleanup()
    print("✅ Shutdown complete!")


# Create FastAPI app
app = FastAPI(
    title="Amazon Product Analysis System",
    description="AI-powered Amazon product analysis with multi-agent workflow",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3001", "http://127.0.0.1:3001"],  # Next.js ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for analysis results (in production, use Redis/Database)
analysis_results: Dict[str, Dict[str, Any]] = {}
analysis_status: Dict[str, str] = {}


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Amazon Product Analysis System API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "analyze": "POST /api/analyze",
            "status": "GET /api/analysis/{session_id}/status",
            "result": "GET /api/analysis/{session_id}/result",
            "websocket": "WS /ws/{session_id}"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "Amazon Product Analysis System"
    }


@app.post("/api/analyze", response_model=AnalysisResponse)
async def analyze_amazon_product(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks
):
    """
    Start Amazon product analysis workflow
    
    This endpoint initiates the multi-agent analysis workflow:
    1. Data Collection (scrape product + find competitors)
    2. Market Analysis (analyze product + competitive positioning)
    3. Optimization Recommendations (generate actionable strategies)
    """
    # Generate session ID
    session_id = str(uuid.uuid4())
    
    # Validate Amazon URL
    url_str = str(request.amazon_url)
    if "amazon.com" not in url_str and "amazon." not in url_str:
        raise HTTPException(
            status_code=400,
            detail="Invalid Amazon URL. Please provide a valid Amazon product URL."
        )
    
    # Initialize analysis status
    analysis_status[session_id] = "started"
    analysis_results[session_id] = {
        "session_id": session_id,
        "amazon_url": url_str,
        "status": "started",
        "started_at": datetime.now().isoformat(),
        "completed_at": None,
        "result": None,
        "error": None
    }
    
    # Start analysis in background
    background_tasks.add_task(run_analysis_workflow, session_id, url_str)
    
    return AnalysisResponse(
        session_id=session_id,
        status="started",
        message="Analysis workflow started. Use WebSocket or polling to track progress.",
        amazon_url=url_str
    )


async def run_analysis_workflow(session_id: str, amazon_url: str):
    """
    Run the complete analysis workflow in background
    """
    try:
        # Small delay to allow WebSocket connection to establish
        await asyncio.sleep(0.5)
        
        # Update status
        analysis_status[session_id] = "running"
        analysis_results[session_id]["status"] = "running"
        
        # Send initial WebSocket notification
        await websocket_manager.send_agent_progress(
            session_id=session_id,
            agent_name="supervisor",
            status="started",
            progress=0.0,
            current_task="Initializing analysis workflow",
            thinking_step="Starting multi-agent Amazon product analysis..."
        )
        
        # Simulate agent progress updates in background
        async def send_progress_updates():
            await asyncio.sleep(2)
            await websocket_manager.send_agent_progress(
                session_id=session_id,
                agent_name="data_collector",
                status="working",
                progress=0.2,
                current_task="Collecting product data",
                thinking_step="Scraping main product and searching for competitors..."
            )
            
            await asyncio.sleep(5)
            await websocket_manager.send_agent_progress(
                session_id=session_id,
                agent_name="data_collector",
                status="completed",
                progress=1.0,
                current_task="Data collection complete",
                thinking_step="Successfully collected product and competitor data"
            )
            
            await asyncio.sleep(1)
            await websocket_manager.send_agent_progress(
                session_id=session_id,
                agent_name="market_analyzer",
                status="working",
                progress=0.5,
                current_task="Analyzing market position",
                thinking_step="Comparing product features and pricing..."
            )
            
            await asyncio.sleep(3)
            await websocket_manager.send_agent_progress(
                session_id=session_id,
                agent_name="market_analyzer",
                status="completed",
                progress=1.0,
                current_task="Market analysis complete",
                thinking_step="Identified key market insights and positioning"
            )
            
            await asyncio.sleep(1)
            await websocket_manager.send_agent_progress(
                session_id=session_id,
                agent_name="optimization_advisor",
                status="working",
                progress=0.7,
                current_task="Generating optimization strategies",
                thinking_step="Creating actionable recommendations..."
            )
        
        # Start progress updates in background
        asyncio.create_task(send_progress_updates())
        
        # Run the analysis workflow asynchronously to avoid blocking
        from concurrent.futures import ThreadPoolExecutor
        
        # Create a separate thread pool for the analysis
        executor = ThreadPoolExecutor(max_workers=1)
        
        # Run the sync analysis in the executor with timeout
        try:
            result = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(
                    executor,
                    analyze_product,
                    amazon_url,
                    session_id
                ),
                timeout=180  # 3 minute timeout
            )
        except asyncio.TimeoutError:
            print(f"Analysis timeout for session {session_id}")
            result = {
                "success": False,
                "error": "Analysis timed out after 3 minutes"
            }
        finally:
            # Clean up the executor
            executor.shutdown(wait=False)
        
        if result.get("success"):
            # Analysis completed successfully
            analysis_status[session_id] = "completed"
            analysis_results[session_id].update({
                "status": "completed",
                "completed_at": datetime.now().isoformat(),
                "result": result
            })
            
            # Send completion notification
            await websocket_manager.send_agent_progress(
                session_id=session_id,
                agent_name="supervisor",
                status="completed",
                progress=1.0,
                current_task="Analysis complete",
                thinking_step="Successfully completed all analysis phases",
                result=result
            )
            
        else:
            # Analysis failed
            error_msg = result.get("error", "Unknown error occurred")
            analysis_status[session_id] = "failed"
            analysis_results[session_id].update({
                "status": "failed",
                "completed_at": datetime.now().isoformat(),
                "error": error_msg
            })
            
            # Send error notification
            await websocket_manager.send_agent_progress(
                session_id=session_id,
                agent_name="supervisor",
                status="error",
                progress=0.0,
                current_task="Analysis failed",
                error_message=error_msg
            )
            
    except Exception as e:
        # Handle unexpected errors
        error_msg = f"Workflow execution error: {str(e)}"
        analysis_status[session_id] = "failed"
        analysis_results[session_id].update({
            "status": "failed",
            "completed_at": datetime.now().isoformat(),
            "error": error_msg
        })
        
        # Send error notification
        await websocket_manager.send_agent_progress(
            session_id=session_id,
            agent_name="supervisor",
            status="error",
            progress=0.0,
            current_task="Unexpected error",
            error_message=error_msg
        )


@app.get("/api/analysis/{session_id}/status")
async def get_analysis_status(session_id: str):
    """
    Get the current status of an analysis session
    """
    if session_id not in analysis_status:
        raise HTTPException(status_code=404, detail="Analysis session not found")
    
    return {
        "session_id": session_id,
        "status": analysis_status[session_id],
        "details": analysis_results.get(session_id, {})
    }


@app.get("/api/analysis/{session_id}/result")
async def get_analysis_result(session_id: str):
    """
    Get the complete analysis result for a session
    """
    if session_id not in analysis_results:
        raise HTTPException(status_code=404, detail="Analysis session not found")
    
    result_data = analysis_results[session_id]
    
    if result_data["status"] == "running":
        return {
            "session_id": session_id,
            "status": "running",
            "message": "Analysis still in progress. Please wait or use WebSocket for real-time updates."
        }
    elif result_data["status"] == "failed":
        return {
            "session_id": session_id,
            "status": "failed",
            "error": result_data.get("error"),
            "started_at": result_data.get("started_at"),
            "completed_at": result_data.get("completed_at")
        }
    else:
        return result_data


@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time analysis progress updates
    """
    await websocket_manager.connect(websocket, session_id)
    
    try:
        # Send initial connection confirmation
        await websocket_manager.send_message(session_id, {
            "type": "connection",
            "message": "Connected to analysis progress stream",
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        })
        
        # Keep connection alive and handle messages
        while True:
            try:
                # Wait for messages from client (heartbeat, etc.)
                data = await websocket.receive_text()
                
                # Handle client messages if needed
                if data == "ping":
                    await websocket_manager.send_message(session_id, {
                        "type": "pong",
                        "timestamp": datetime.now().isoformat()
                    })
                    
            except WebSocketDisconnect:
                break
            except Exception as e:
                print(f"WebSocket error: {e}")
                break
                
    except WebSocketDisconnect:
        pass
    finally:
        await websocket_manager.disconnect(session_id)


@app.get("/api/sessions")
async def list_active_sessions():
    """
    List all active analysis sessions (for debugging/monitoring)
    """
    return {
        "active_sessions": list(analysis_status.keys()),
        "session_details": {
            session_id: {
                "status": status,
                "started_at": analysis_results.get(session_id, {}).get("started_at"),
                "url": analysis_results.get(session_id, {}).get("amazon_url")
            }
            for session_id, status in analysis_status.items()
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    # Load environment variables from project root
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
    
    # Run the application
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )