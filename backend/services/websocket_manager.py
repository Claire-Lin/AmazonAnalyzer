"""
WebSocket Manager for Real-time Agent Progress Updates

This module manages WebSocket connections for real-time communication
between the backend agents and frontend client during analysis workflow.
"""

import json
import asyncio
from typing import Dict, Optional, Any, List
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect
from models.database import db_manager


class WebSocketManager:
    """
    Manager for WebSocket connections and real-time updates
    """
    
    def __init__(self):
        # Active connections: session_id -> WebSocket
        self.active_connections: Dict[str, WebSocket] = {}
        
        # Connection metadata
        self.connection_metadata: Dict[str, Dict[str, Any]] = {}
        
        # Message buffer for messages sent before connection: session_id -> List[messages]
        self.message_buffer: Dict[str, List[Dict[str, Any]]] = {}
        
    def initialize(self):
        """Initialize the WebSocket manager"""
        print("🌐 WebSocket Manager initialized")
        
    async def connect(self, websocket: WebSocket, session_id: str):
        """
        Connect a new WebSocket client
        """
        await websocket.accept()
        self.active_connections[session_id] = websocket
        self.connection_metadata[session_id] = {
            "connected_at": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat()
        }
        print(f"🔌 WebSocket connected for session: {session_id}")
        
        # Send any buffered messages for this session
        if session_id in self.message_buffer and self.message_buffer[session_id]:
            print(f"📨 Sending {len(self.message_buffer[session_id])} buffered messages for session: {session_id}")
            for message in self.message_buffer[session_id]:
                try:
                    await websocket.send_text(json.dumps(message))
                    await asyncio.sleep(0.01)  # Small delay to prevent overwhelming the client
                except Exception as e:
                    print(f"Error sending buffered message: {e}")
            # Clear the buffer after sending
            self.message_buffer[session_id] = []
        
    async def disconnect(self, session_id: str):
        """
        Disconnect a WebSocket client
        """
        was_connected = session_id in self.active_connections
        if session_id in self.active_connections:
            del self.active_connections[session_id]
        if session_id in self.connection_metadata:
            del self.connection_metadata[session_id]
        
        # Only log if there was actually a connection to disconnect
        if was_connected:
            print(f"🔌 WebSocket disconnected for session: {session_id}")
        
    async def send_message(self, session_id: str, message: Dict[str, Any]):
        """
        Send a message to a specific session
        """
        if session_id in self.active_connections:
            websocket = self.active_connections[session_id]
            try:
                await websocket.send_text(json.dumps(message))
                
                # Update last activity
                if session_id in self.connection_metadata:
                    self.connection_metadata[session_id]["last_activity"] = datetime.now().isoformat()
                    
            except WebSocketDisconnect:
                await self.disconnect(session_id)
            except Exception as e:
                print(f"Error sending WebSocket message to {session_id}: {e}")
                await self.disconnect(session_id)
        else:
            # No active connection, buffer the message
            if session_id not in self.message_buffer:
                self.message_buffer[session_id] = []
            self.message_buffer[session_id].append(message)
            print(f"📥 Buffered message for disconnected session {session_id} (total buffered: {len(self.message_buffer[session_id])})")
        
    async def broadcast_message(self, message: Dict[str, Any]):
        """
        Broadcast a message to all connected clients
        """
        disconnected_sessions = []
        
        for session_id, websocket in self.active_connections.items():
            try:
                await websocket.send_text(json.dumps(message))
            except WebSocketDisconnect:
                disconnected_sessions.append(session_id)
            except Exception as e:
                print(f"Error broadcasting to {session_id}: {e}")
                disconnected_sessions.append(session_id)
        
        # Clean up disconnected sessions
        for session_id in disconnected_sessions:
            await self.disconnect(session_id)
    
    async def send_agent_progress(
        self,
        session_id: str,
        agent_name: str,
        status: str,
        progress: float,
        current_task: str,
        thinking_step: Optional[str] = None,
        error_message: Optional[str] = None,
        result: Optional[Dict[str, Any]] = None
    ):
        """
        Send agent progress update to client
        """
        message = {
            "type": "agent_progress",
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "data": {
                "agent_name": agent_name,
                "status": status,
                "progress": progress,
                "current_task": current_task,
                "thinking_step": thinking_step,
                "error_message": error_message,
                "result": result
            }
        }
        
        # Send via WebSocket
        await self.send_message(session_id, message)
        
        # Save to database for persistence
        db_manager.save_agent_progress(
            session_id=session_id,
            agent_name=agent_name,
            status=status,
            progress=progress,
            current_task=current_task,
            thinking_step=thinking_step,
            error_message=error_message,
            result_data=result
        )
        
        print(f"📡 Agent progress: {agent_name} - {current_task} ({progress*100:.1f}%)")
    
    async def send_workflow_status(
        self,
        session_id: str,
        workflow_status: str,
        current_phase: str,
        message: str,
        progress: Optional[float] = None
    ):
        """
        Send overall workflow status update
        """
        message_data = {
            "type": "workflow_status",
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "data": {
                "status": workflow_status,
                "current_phase": current_phase,
                "message": message,
                "progress": progress
            }
        }
        
        await self.send_message(session_id, message_data)
        print(f"📊 Workflow status: {current_phase} - {message}")
    
    async def send_analysis_complete(
        self,
        session_id: str,
        result: Dict[str, Any],
        success: bool = True
    ):
        """
        Send analysis completion notification
        """
        message = {
            "type": "analysis_complete",
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "data": {
                "success": success,
                "result": result,
                "message": "Analysis completed successfully!" if success else "Analysis failed"
            }
        }
        
        await self.send_message(session_id, message)
        print(f"✅ Analysis complete notification sent for session: {session_id}")
    
    async def send_error(
        self,
        session_id: str,
        error_type: str,
        error_message: str,
        agent_name: Optional[str] = None
    ):
        """
        Send error notification to client
        """
        message = {
            "type": "error",
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "data": {
                "error_type": error_type,
                "error_message": error_message,
                "agent_name": agent_name
            }
        }
        
        await self.send_message(session_id, message)
        print(f"❌ Error notification: {error_type} - {error_message}")
    
    def get_active_connections(self) -> Dict[str, Dict[str, Any]]:
        """
        Get information about active connections
        """
        return {
            session_id: {
                "connected_at": metadata.get("connected_at"),
                "last_activity": metadata.get("last_activity"),
                "is_connected": session_id in self.active_connections
            }
            for session_id, metadata in self.connection_metadata.items()
        }
    
    async def ping_clients(self):
        """
        Send ping to all connected clients to check connectivity
        """
        ping_message = {
            "type": "ping",
            "timestamp": datetime.now().isoformat()
        }
        
        await self.broadcast_message(ping_message)
    
    async def cleanup(self):
        """
        Clean up all connections during shutdown
        """
        print("🧹 Cleaning up WebSocket connections...")
        
        # Close all active connections
        for session_id in list(self.active_connections.keys()):
            try:
                websocket = self.active_connections[session_id]
                await websocket.close()
            except Exception as e:
                print(f"Error closing WebSocket for {session_id}: {e}")
            finally:
                await self.disconnect(session_id)
        
        # Clear message buffers
        self.message_buffer.clear()
        
        print("✅ WebSocket cleanup complete")
    
    def clean_old_buffers(self, max_age_minutes: int = 30):
        """
        Clean up old message buffers to prevent memory leaks
        """
        # This would be called periodically to clean up buffers for sessions that never connected
        # For now, we'll keep it simple and clear buffers when they're sent


# Global WebSocket manager instance
websocket_manager = WebSocketManager()


# Utility functions for agent integration
async def notify_agent_start(session_id: str, agent_name: str, task_description: str):
    """Utility function to notify agent start"""
    await websocket_manager.send_agent_progress(
        session_id=session_id,
        agent_name=agent_name,
        status="working",
        progress=0.0,
        current_task=f"Starting {agent_name.replace('_', ' ')}",
        thinking_step=task_description
    )


async def notify_agent_progress(session_id: str, agent_name: str, progress: float, 
                              task: str, thinking: str):
    """Utility function to notify agent progress"""
    await websocket_manager.send_agent_progress(
        session_id=session_id,
        agent_name=agent_name,
        status="working",
        progress=progress,
        current_task=task,
        thinking_step=thinking
    )


async def notify_agent_complete(session_id: str, agent_name: str, result: Dict[str, Any]):
    """Utility function to notify agent completion"""
    await websocket_manager.send_agent_progress(
        session_id=session_id,
        agent_name=agent_name,
        status="completed",
        progress=1.0,
        current_task=f"{agent_name.replace('_', ' ')} completed",
        thinking_step="Analysis phase completed successfully",
        result=result
    )


async def notify_agent_error(session_id: str, agent_name: str, error_message: str):
    """Utility function to notify agent error"""
    await websocket_manager.send_agent_progress(
        session_id=session_id,
        agent_name=agent_name,
        status="error",
        progress=0.0,
        current_task="Error occurred",
        error_message=error_message
    )