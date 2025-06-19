"""
Utility functions for sending WebSocket notifications from synchronous contexts
"""
import asyncio
import threading
from typing import Optional, Dict, Any
from concurrent.futures import ThreadPoolExecutor

# Global executor for running async tasks
_executor = ThreadPoolExecutor(max_workers=2)

def send_websocket_notification_sync(
    websocket_manager,
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
    Send WebSocket notification from a synchronous context
    """
    def _run_async_in_thread():
        """Run the async function in a new thread with its own event loop"""
        async def _send_notification():
            try:
                await websocket_manager.send_agent_progress(
                    session_id=session_id,
                    agent_name=agent_name,
                    status=status,
                    progress=progress,
                    current_task=current_task,
                    thinking_step=thinking_step,
                    error_message=error_message,
                    result=result
                )
            except Exception as e:
                print(f"WebSocket send_agent_progress failed: {e}")
        
        # Create new event loop for this thread
        loop = None
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(_send_notification())
        except Exception as e:
            print(f"Failed to run async notification in thread: {e}")
        finally:
            if loop:
                try:
                    loop.close()
                except:
                    pass
            # Clear the event loop for this thread
            try:
                asyncio.set_event_loop(None)
            except:
                pass
    
    try:
        # Always use a separate thread to avoid any event loop conflicts
        thread = threading.Thread(target=_run_async_in_thread, daemon=True)
        thread.start()
        # Fire and forget - don't wait for completion
    except Exception as e:
        print(f"Failed to create WebSocket notification thread: {e}")