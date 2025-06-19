"""
Pydantic models for Amazon Product Analysis System API

This module contains all the data models used by the FastAPI application
for request/response validation and documentation.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, HttpUrl, Field
from enum import Enum


class AnalysisStatus(str, Enum):
    """Analysis workflow status enum"""
    STARTED = "started"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentStatus(str, Enum):
    """Individual agent status enum"""
    WORKING = "working"
    COMPLETED = "completed"
    ERROR = "error"


class AnalysisRequest(BaseModel):
    """Request model for Amazon product analysis"""
    amazon_url: HttpUrl = Field(
        ...,
        description="Amazon product URL to analyze",
        example="https://www.amazon.com/dp/B08N5WRWNW"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "amazon_url": "https://www.amazon.com/Tamagotchi-Nano-Peanuts-Silicone-Case/dp/B0FB7FQWJL"
            }
        }


class AnalysisResponse(BaseModel):
    """Response model for analysis initiation"""
    session_id: str = Field(..., description="Unique session ID for tracking progress")
    status: AnalysisStatus = Field(..., description="Current analysis status")
    message: str = Field(..., description="Human-readable status message")
    amazon_url: str = Field(..., description="The Amazon URL being analyzed")
    started_at: Optional[str] = Field(None, description="ISO timestamp when analysis started")
    
    class Config:
        schema_extra = {
            "example": {
                "session_id": "123e4567-e89b-12d3-a456-426614174000",
                "status": "started",
                "message": "Analysis workflow started. Use WebSocket or polling to track progress.",
                "amazon_url": "https://www.amazon.com/dp/B08N5WRWNW",
                "started_at": "2024-01-15T10:30:00Z"
            }
        }


class ProductData(BaseModel):
    """Model for scraped product data"""
    title: Optional[str] = None
    price: Optional[float] = None
    currency: Optional[str] = None
    brand: Optional[str] = None
    asin: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None
    specifications: Optional[str] = None
    reviews: Optional[List[str]] = None
    rating: Optional[float] = None
    review_count: Optional[str] = None
    url: str
    timestamp: str
    success: bool = True


class AgentProgress(BaseModel):
    """Model for agent progress updates via WebSocket"""
    agent_name: str = Field(..., description="Name of the agent (data_collector, market_analyzer, etc.)")
    status: AgentStatus = Field(..., description="Current agent status")
    progress: float = Field(..., ge=0.0, le=1.0, description="Progress percentage (0.0 to 1.0)")
    current_task: str = Field(..., description="Description of current task")
    thinking_step: Optional[str] = Field(None, description="Current reasoning or processing step")
    error_message: Optional[str] = Field(None, description="Error message if status is error")
    result: Optional[Dict[str, Any]] = Field(None, description="Partial or final result data")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    
    class Config:
        schema_extra = {
            "example": {
                "agent_name": "data_collector",
                "status": "working",
                "progress": 0.6,
                "current_task": "Scraping competitor products",
                "thinking_step": "Found 5 competitor products, scraping detailed information...",
                "timestamp": "2024-01-15T10:35:00Z"
            }
        }


class WebSocketMessage(BaseModel):
    """Model for WebSocket messages"""
    type: str = Field(..., description="Message type")
    session_id: str = Field(..., description="Session ID")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    data: Optional[Dict[str, Any]] = Field(None, description="Message payload")
    
    class Config:
        schema_extra = {
            "example": {
                "type": "agent_progress",
                "session_id": "123e4567-e89b-12d3-a456-426614174000",
                "timestamp": "2024-01-15T10:35:00Z",
                "data": {
                    "agent_name": "data_collector",
                    "status": "working",
                    "progress": 0.6,
                    "current_task": "Scraping competitor products"
                }
            }
        }


class AnalysisResult(BaseModel):
    """Complete analysis result model"""
    session_id: str
    amazon_url: str
    status: AnalysisStatus
    started_at: str
    completed_at: Optional[str] = None
    
    # Analysis data
    main_product_data: Optional[ProductData] = None
    competitor_data: Optional[List[ProductData]] = None
    product_analysis: Optional[str] = None
    competitor_analysis: Optional[str] = None
    market_positioning: Optional[str] = None
    optimization_strategy: Optional[str] = None
    
    # Error handling
    error: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "session_id": "123e4567-e89b-12d3-a456-426614174000",
                "amazon_url": "https://www.amazon.com/dp/B08N5WRWNW",
                "status": "completed",
                "started_at": "2024-01-15T10:30:00Z",
                "completed_at": "2024-01-15T10:45:00Z",
                "main_product_data": {
                    "title": "Echo Dot (4th Gen) - Smart speaker with Alexa",
                    "price": 49.99,
                    "currency": "USD",
                    "brand": "Amazon",
                    "asin": "B08N5WRWNW"
                },
                "product_analysis": "Comprehensive product analysis...",
                "optimization_strategy": "Detailed optimization recommendations..."
            }
        }


class SessionStatus(BaseModel):
    """Model for session status response"""
    session_id: str
    status: AnalysisStatus
    details: Dict[str, Any]
    
    class Config:
        schema_extra = {
            "example": {
                "session_id": "123e4567-e89b-12d3-a456-426614174000",
                "status": "running",
                "details": {
                    "amazon_url": "https://www.amazon.com/dp/B08N5WRWNW",
                    "started_at": "2024-01-15T10:30:00Z",
                    "current_phase": "market_analysis"
                }
            }
        }


class ActiveSessions(BaseModel):
    """Model for active sessions list"""
    active_sessions: List[str]
    session_details: Dict[str, Dict[str, Any]]
    
    class Config:
        schema_extra = {
            "example": {
                "active_sessions": ["123e4567-e89b-12d3-a456-426614174000"],
                "session_details": {
                    "123e4567-e89b-12d3-a456-426614174000": {
                        "status": "running",
                        "started_at": "2024-01-15T10:30:00Z",
                        "url": "https://www.amazon.com/dp/B08N5WRWNW"
                    }
                }
            }
        }