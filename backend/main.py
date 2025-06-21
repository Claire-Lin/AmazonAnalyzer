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

# Import our agents and services
from agents.supervisor import analyze_product
from services.websocket_manager import websocket_manager
from services.redis_manager import redis_manager, init_redis, cleanup_redis
from models.database import init_db, db_manager
from models.analysis import AnalysisRequest, AnalysisResponse, AnalysisStatus


# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Starting Amazon Product Analysis System...")
    
    # Initialize database
    await init_db()
    
    # Initialize Redis
    await init_redis()
    
    # Initialize WebSocket manager
    websocket_manager.initialize()
    
    print("✅ System initialized successfully!")
    
    yield
    
    # Shutdown
    print("🔄 Shutting down Amazon Product Analysis System...")
    await websocket_manager.cleanup()
    await cleanup_redis()
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

# Note: Using Redis + PostgreSQL for persistent storage instead of in-memory dictionaries


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Amazon Product Analysis System API",
        "version": "1.0.0",
        "storage": "Redis + PostgreSQL",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "analyze": "POST /api/analyze",
            "status": "GET /api/analysis/{session_id}/status",
            "result": "GET /api/analysis/{session_id}/result",
            "detailed_result": "GET /api/analysis/{session_id}/detailed",
            "websocket": "WS /ws/{session_id}",
            "sessions": "GET /api/sessions",
            "database_sessions": "GET /api/database/sessions"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    # Check Redis connection
    redis_status = "connected" if redis_manager.connected else "disconnected"
    
    # Check PostgreSQL connection (simple test)
    db_status = "connected"
    try:
        test_session = db_manager.get_analysis_session("health_check_test")
        # If no exception, database is accessible
    except Exception:
        db_status = "disconnected"
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "Amazon Product Analysis System",
        "redis_status": redis_status,
        "database_status": db_status,
        "storage": "Redis + PostgreSQL"
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
    
    # Initialize analysis status in Redis and PostgreSQL
    session_data = {
        "session_id": session_id,
        "amazon_url": url_str,
        "status": "started",
        "started_at": datetime.now().isoformat(),
        "completed_at": None,
        "result": None,
        "error": None
    }
    
    # Save to Redis (fast access)
    await redis_manager.set_analysis_status(session_id, "started")
    await redis_manager.save_session(session_id, session_data)
    
    # Save to PostgreSQL (persistent storage)
    db_manager.save_analysis_session(session_id, url_str, "started")
    
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
        
        # Update status in Redis and PostgreSQL
        await redis_manager.set_analysis_status(session_id, "running")
        await redis_manager.update_session(session_id, {"status": "running"})
        db_manager.update_analysis_session(session_id, status="running")
        
        # Send initial WebSocket notification
        await websocket_manager.send_agent_progress(
            session_id=session_id,
            agent_name="supervisor",
            status="started",
            progress=0.0,
            current_task="Initializing analysis workflow",
            thinking_step="Starting multi-agent Amazon product analysis..."
        )
        
        # Note: Progress updates are now handled by individual agents and tools
        # The background progress simulation has been removed to avoid timing conflicts
        # Real progress is tracked through WebSocket notifications in each agent/tool
        
        # Run the analysis workflow asynchronously to avoid blocking
        from concurrent.futures import ThreadPoolExecutor
        
        # Create a separate thread pool for the analysis
        executor = ThreadPoolExecutor(max_workers=1)
        
        # Run the sync analysis in the executor without timeout
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                executor,
                analyze_product,
                amazon_url,
                session_id
            )
        except Exception as e:
            print(f"Analysis error for session {session_id}: {str(e)}")
            result = {
                "success": False,
                "error": f"Analysis failed: {str(e)}"
            }
        finally:
            # Clean up the executor
            executor.shutdown(wait=False)
        
        if result.get("success"):
            # Analysis completed successfully
            completion_time = datetime.now().isoformat()
            
            # Update Redis
            await redis_manager.set_analysis_status(session_id, "completed")
            await redis_manager.update_session(session_id, {
                "status": "completed",
                "completed_at": completion_time,
                "result": result
            })
            await redis_manager.save_analysis_result(session_id, result)
            
            # Update PostgreSQL
            db_manager.update_analysis_session(
                session_id, 
                status="completed",
                completed_at=datetime.fromisoformat(completion_time),
                product_analysis=result.get("market_analysis"),
                optimization_strategy=result.get("optimization_results")
            )
            
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
            completion_time = datetime.now().isoformat()
            
            # Update Redis
            await redis_manager.set_analysis_status(session_id, "failed")
            await redis_manager.update_session(session_id, {
                "status": "failed",
                "completed_at": completion_time,
                "error": error_msg
            })
            
            # Update PostgreSQL
            db_manager.update_analysis_session(
                session_id,
                status="failed",
                completed_at=datetime.fromisoformat(completion_time),
                error_message=error_msg
            )
            
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
        completion_time = datetime.now().isoformat()
        
        # Update Redis
        await redis_manager.set_analysis_status(session_id, "failed")
        await redis_manager.update_session(session_id, {
            "status": "failed",
            "completed_at": completion_time,
            "error": error_msg
        })
        
        # Update PostgreSQL
        db_manager.update_analysis_session(
            session_id,
            status="failed",
            completed_at=datetime.fromisoformat(completion_time),
            error_message=error_msg
        )
        
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
    # Try Redis first (fast)
    status = await redis_manager.get_analysis_status(session_id)
    session_data = await redis_manager.get_session(session_id)
    
    # Fallback to PostgreSQL if not in Redis
    if not status or not session_data:
        db_session = db_manager.get_analysis_session(session_id)
        if db_session:
            status = db_session.status
            session_data = {
                "session_id": db_session.session_id,
                "amazon_url": db_session.amazon_url,
                "status": db_session.status,
                "started_at": db_session.started_at.isoformat() if db_session.started_at else None,
                "completed_at": db_session.completed_at.isoformat() if db_session.completed_at else None,
                "error": db_session.error_message
            }
            # Cache in Redis for next time
            await redis_manager.set_analysis_status(session_id, status)
            await redis_manager.save_session(session_id, session_data)
        else:
            raise HTTPException(status_code=404, detail="Analysis session not found")
    
    return {
        "session_id": session_id,
        "status": status,
        "details": session_data
    }


@app.get("/api/analysis/{session_id}/result")
async def get_analysis_result(session_id: str):
    """
    Get the complete analysis result for a session
    """
    # Try Redis first (fast)
    result_data = await redis_manager.get_analysis_result(session_id)
    session_data = await redis_manager.get_session(session_id)
    
    # Fallback to PostgreSQL if not in Redis
    if not result_data or not session_data:
        db_session = db_manager.get_analysis_session(session_id)
        if db_session:
            session_data = {
                "session_id": db_session.session_id,
                "amazon_url": db_session.amazon_url,
                "status": db_session.status,
                "started_at": db_session.started_at.isoformat() if db_session.started_at else None,
                "completed_at": db_session.completed_at.isoformat() if db_session.completed_at else None,
                "error": db_session.error_message
            }
            
            # Try to get result from database analysis fields
            if db_session.status == "completed":
                result_data = {
                    "success": True,
                    "market_analysis": db_session.product_analysis,
                    "optimization_results": db_session.optimization_strategy,
                    "session_id": session_id
                }
                # Cache in Redis for next time
                await redis_manager.save_analysis_result(session_id, result_data)
                await redis_manager.save_session(session_id, session_data)
        else:
            raise HTTPException(status_code=404, detail="Analysis session not found")
    
    status = session_data.get("status", "unknown")
    
    if status == "running":
        return {
            "session_id": session_id,
            "status": "running",
            "message": "Analysis still in progress. Please wait or use WebSocket for real-time updates."
        }
    elif status == "failed":
        return {
            "session_id": session_id,
            "status": "failed",
            "error": session_data.get("error"),
            "started_at": session_data.get("started_at"),
            "completed_at": session_data.get("completed_at")
        }
    else:
        # Return complete result
        return {
            **session_data,
            "result": result_data
        }


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


@app.get("/api/analysis/{session_id}/detailed")
async def get_detailed_analysis_result(session_id: str):
    """
    Get comprehensive analysis result with all database data including products and analysis details
    """
    # Get session from database
    db_session = db_manager.get_analysis_session(session_id)
    if not db_session:
        raise HTTPException(status_code=404, detail="Analysis session not found")
    
    # Get all products for this session
    products = db_manager.get_session_products(session_id)
    
    # Separate main product and competitors
    main_product = None
    competitors = []
    
    for product in products:
        product_data = {
            "asin": product.asin,
            "url": product.url,
            "title": product.title,
            "brand": product.brand,
            "price": product.price,
            "currency": product.currency,
            "description": product.description,
            "color": product.color,
            "specifications": product.specifications,
            "reviews": product.reviews,
            "rating": product.rating,
            "review_count": product.review_count,
            "scraped_at": product.scraped_at.isoformat() if product.scraped_at else None,
            "scrape_success": product.scrape_success
        }
        
        if product.is_main_product:
            main_product = product_data
        elif product.is_competitor:
            competitors.append(product_data)
    
    return {
        "session_id": session_id,
        "amazon_url": db_session.amazon_url,
        "status": db_session.status,
        "started_at": db_session.started_at.isoformat() if db_session.started_at else None,
        "completed_at": db_session.completed_at.isoformat() if db_session.completed_at else None,
        "error_message": db_session.error_message,
        
        # Product data
        "main_product": main_product,
        "competitors": competitors,
        "total_products_found": len(products),
        
        # Analysis results
        "product_analysis": db_session.product_analysis,
        "competitor_analysis": db_session.competitor_analysis,
        "market_positioning": db_session.market_positioning,
        "optimization_strategy": db_session.optimization_strategy,
        
        # Metadata
        "created_at": db_session.created_at.isoformat() if db_session.created_at else None,
        "updated_at": db_session.updated_at.isoformat() if db_session.updated_at else None
    }


@app.get("/api/sessions")
async def list_active_sessions():
    """
    List all active analysis sessions (for debugging/monitoring)
    """
    # Get active WebSocket sessions from Redis
    websocket_sessions = await redis_manager.get_websocket_sessions()
    
    # Also get Redis stats for monitoring
    redis_stats = await redis_manager.get_stats()
    
    return {
        "active_websocket_sessions": websocket_sessions,
        "redis_stats": redis_stats,
        "message": "Session data now persisted in Redis + PostgreSQL"
    }


@app.get("/api/database/sessions")
async def list_database_sessions():
    """
    List all analysis sessions from the database
    """
    try:
        from models.database import SessionLocal, AnalysisSession
        db = SessionLocal()
        
        # Get recent sessions (last 50)
        sessions = db.query(AnalysisSession).order_by(
            AnalysisSession.created_at.desc()
        ).limit(50).all()
        
        session_list = []
        for session in sessions:
            session_list.append({
                "session_id": session.session_id,
                "amazon_url": session.amazon_url,
                "status": session.status,
                "started_at": session.started_at.isoformat() if session.started_at else None,
                "completed_at": session.completed_at.isoformat() if session.completed_at else None,
                "has_product_analysis": bool(session.product_analysis),
                "has_competitor_analysis": bool(session.competitor_analysis),
                "has_market_positioning": bool(session.market_positioning),
                "has_optimization_strategy": bool(session.optimization_strategy),
                "error_message": session.error_message,
                "created_at": session.created_at.isoformat() if session.created_at else None
            })
        
        db.close()
        
        return {
            "total_sessions": len(session_list),
            "sessions": session_list
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


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