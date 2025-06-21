"""
Redis Manager for Amazon Product Analysis System

This module provides Redis-based caching and session management
for improved performance and scalability.
"""

import os
import json
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import redis.asyncio as aioredis
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))

class RedisManager:
    """
    Redis manager for caching analysis results, session data, and WebSocket connections
    """
    
    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.redis_client: Optional[aioredis.Redis] = None
        self.connected = False
        
        # Key prefixes for different data types
        self.SESSION_PREFIX = "session:"
        self.RESULT_PREFIX = "result:"
        self.STATUS_PREFIX = "status:"
        self.PROGRESS_PREFIX = "progress:"
        self.WEBSOCKET_PREFIX = "ws:"
        self.CACHE_PREFIX = "cache:"
        
        # Default TTL (Time To Live) in seconds
        self.DEFAULT_TTL = 3600  # 1 hour
        self.SESSION_TTL = 7200  # 2 hours
        self.CACHE_TTL = 1800    # 30 minutes
    
    async def initialize(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            
            # Test connection
            await self.redis_client.ping()
            self.connected = True
            print(f"✅ Redis connected successfully: {self.redis_url}")
            return True
            
        except Exception as e:
            print(f"⚠️  Redis connection failed: {e}")
            print("   Falling back to in-memory storage")
            self.connected = False
            return False
    
    async def close(self):
        """Close Redis connection"""
        if self.redis_client and self.connected:
            await self.redis_client.close()
            self.connected = False
            print("✅ Redis connection closed")
    
    def _get_key(self, prefix: str, identifier: str) -> str:
        """Generate Redis key with prefix"""
        return f"{prefix}{identifier}"
    
    async def _safe_execute(self, operation, *args, **kwargs):
        """Safely execute Redis operation with fallback"""
        if not self.connected or not self.redis_client:
            return None
        
        try:
            return await operation(*args, **kwargs)
        except Exception as e:
            print(f"Redis operation failed: {e}")
            return None
    
    # Session Management
    async def save_session(self, session_id: str, session_data: Dict[str, Any], ttl: int = None) -> bool:
        """Save analysis session data to Redis"""
        key = self._get_key(self.SESSION_PREFIX, session_id)
        ttl = ttl or self.SESSION_TTL
        
        try:
            session_json = json.dumps(session_data, default=str)
            result = await self._safe_execute(
                self.redis_client.setex,
                key, ttl, session_json
            )
            return result is not None
        except Exception as e:
            print(f"Failed to save session {session_id}: {e}")
            return False
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get analysis session data from Redis"""
        key = self._get_key(self.SESSION_PREFIX, session_id)
        
        try:
            session_json = await self._safe_execute(
                self.redis_client.get, key
            )
            if session_json:
                return json.loads(session_json)
            return None
        except Exception as e:
            print(f"Failed to get session {session_id}: {e}")
            return None
    
    async def update_session(self, session_id: str, updates: Dict[str, Any]) -> bool:
        """Update analysis session data"""
        session_data = await self.get_session(session_id)
        if session_data:
            session_data.update(updates)
            session_data["updated_at"] = datetime.now().isoformat()
            return await self.save_session(session_id, session_data)
        return False
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete analysis session from Redis"""
        key = self._get_key(self.SESSION_PREFIX, session_id)
        result = await self._safe_execute(self.redis_client.delete, key)
        return result is not None and result > 0
    
    # Analysis Results Management
    async def save_analysis_result(self, session_id: str, result_data: Dict[str, Any], ttl: int = None) -> bool:
        """Save complete analysis results"""
        key = self._get_key(self.RESULT_PREFIX, session_id)
        ttl = ttl or self.DEFAULT_TTL
        
        try:
            result_json = json.dumps(result_data, default=str)
            result = await self._safe_execute(
                self.redis_client.setex,
                key, ttl, result_json
            )
            return result is not None
        except Exception as e:
            print(f"Failed to save result {session_id}: {e}")
            return False
    
    async def get_analysis_result(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get complete analysis results"""
        key = self._get_key(self.RESULT_PREFIX, session_id)
        
        try:
            result_json = await self._safe_execute(
                self.redis_client.get, key
            )
            if result_json:
                return json.loads(result_json)
            return None
        except Exception as e:
            print(f"Failed to get result {session_id}: {e}")
            return None
    
    # Status Management
    async def set_analysis_status(self, session_id: str, status: str, ttl: int = None) -> bool:
        """Set analysis status"""
        key = self._get_key(self.STATUS_PREFIX, session_id)
        ttl = ttl or self.DEFAULT_TTL
        
        result = await self._safe_execute(
            self.redis_client.setex,
            key, ttl, status
        )
        return result is not None
    
    async def get_analysis_status(self, session_id: str) -> Optional[str]:
        """Get analysis status"""
        key = self._get_key(self.STATUS_PREFIX, session_id)
        return await self._safe_execute(self.redis_client.get, key)
    
    # Progress Tracking
    async def save_agent_progress(self, session_id: str, agent_name: str, progress_data: Dict[str, Any], ttl: int = None) -> bool:
        """Save agent progress data"""
        key = self._get_key(self.PROGRESS_PREFIX, f"{session_id}:{agent_name}")
        ttl = ttl or self.DEFAULT_TTL
        
        try:
            progress_json = json.dumps(progress_data, default=str)
            result = await self._safe_execute(
                self.redis_client.setex,
                key, ttl, progress_json
            )
            return result is not None
        except Exception as e:
            print(f"Failed to save progress {session_id}:{agent_name}: {e}")
            return False
    
    async def get_agent_progress(self, session_id: str, agent_name: str) -> Optional[Dict[str, Any]]:
        """Get agent progress data"""
        key = self._get_key(self.PROGRESS_PREFIX, f"{session_id}:{agent_name}")
        
        try:
            progress_json = await self._safe_execute(
                self.redis_client.get, key
            )
            if progress_json:
                return json.loads(progress_json)
            return None
        except Exception as e:
            print(f"Failed to get progress {session_id}:{agent_name}: {e}")
            return None
    
    async def get_session_progress(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all agent progress for a session"""
        pattern = self._get_key(self.PROGRESS_PREFIX, f"{session_id}:*")
        progress_list = []
        
        try:
            keys = await self._safe_execute(self.redis_client.keys, pattern)
            if keys:
                for key in keys:
                    progress_json = await self._safe_execute(self.redis_client.get, key)
                    if progress_json:
                        progress_list.append(json.loads(progress_json))
        except Exception as e:
            print(f"Failed to get session progress {session_id}: {e}")
        
        return progress_list
    
    # WebSocket Session Management
    async def add_websocket_session(self, session_id: str, connection_info: Dict[str, Any], ttl: int = None) -> bool:
        """Add WebSocket connection info"""
        key = self._get_key(self.WEBSOCKET_PREFIX, session_id)
        ttl = ttl or self.DEFAULT_TTL
        
        try:
            connection_json = json.dumps(connection_info, default=str)
            result = await self._safe_execute(
                self.redis_client.setex,
                key, ttl, connection_json
            )
            return result is not None
        except Exception as e:
            print(f"Failed to add WebSocket session {session_id}: {e}")
            return False
    
    async def remove_websocket_session(self, session_id: str) -> bool:
        """Remove WebSocket connection info"""
        key = self._get_key(self.WEBSOCKET_PREFIX, session_id)
        result = await self._safe_execute(self.redis_client.delete, key)
        return result is not None and result > 0
    
    async def get_websocket_sessions(self) -> List[str]:
        """Get all active WebSocket session IDs"""
        pattern = self._get_key(self.WEBSOCKET_PREFIX, "*")
        try:
            keys = await self._safe_execute(self.redis_client.keys, pattern)
            if keys:
                return [key.replace(self.WEBSOCKET_PREFIX, "") for key in keys]
            return []
        except Exception as e:
            print(f"Failed to get WebSocket sessions: {e}")
            return []
    
    # Generic Caching
    async def cache_set(self, key: str, value: Any, ttl: int = None) -> bool:
        """Set cache value"""
        cache_key = self._get_key(self.CACHE_PREFIX, key)
        ttl = ttl or self.CACHE_TTL
        
        try:
            value_json = json.dumps(value, default=str)
            result = await self._safe_execute(
                self.redis_client.setex,
                cache_key, ttl, value_json
            )
            return result is not None
        except Exception as e:
            print(f"Failed to set cache {key}: {e}")
            return False
    
    async def cache_get(self, key: str) -> Any:
        """Get cache value"""
        cache_key = self._get_key(self.CACHE_PREFIX, key)
        
        try:
            value_json = await self._safe_execute(
                self.redis_client.get, cache_key
            )
            if value_json:
                return json.loads(value_json)
            return None
        except Exception as e:
            print(f"Failed to get cache {key}: {e}")
            return None
    
    async def cache_delete(self, key: str) -> bool:
        """Delete cache value"""
        cache_key = self._get_key(self.CACHE_PREFIX, key)
        result = await self._safe_execute(self.redis_client.delete, cache_key)
        return result is not None and result > 0
    
    # Cleanup and Maintenance
    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions (Redis handles TTL automatically, but this is for manual cleanup)"""
        patterns = [
            self._get_key(self.SESSION_PREFIX, "*"),
            self._get_key(self.RESULT_PREFIX, "*"),
            self._get_key(self.STATUS_PREFIX, "*"),
            self._get_key(self.PROGRESS_PREFIX, "*"),
            self._get_key(self.WEBSOCKET_PREFIX, "*")
        ]
        
        cleaned = 0
        for pattern in patterns:
            try:
                keys = await self._safe_execute(self.redis_client.keys, pattern)
                if keys:
                    # Check TTL for each key and remove if expired
                    for key in keys:
                        ttl = await self._safe_execute(self.redis_client.ttl, key)
                        if ttl is not None and ttl == -1:  # Key exists but has no TTL
                            await self._safe_execute(self.redis_client.expire, key, self.DEFAULT_TTL)
                        elif ttl is not None and ttl == -2:  # Key doesn't exist
                            cleaned += 1
            except Exception as e:
                print(f"Cleanup error for pattern {pattern}: {e}")
        
        return cleaned
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get Redis statistics"""
        try:
            info = await self._safe_execute(self.redis_client.info)
            return {
                "connected": self.connected,
                "redis_url": self.redis_url,
                "memory_usage": info.get("used_memory_human") if info else "N/A",
                "connected_clients": info.get("connected_clients") if info else "N/A",
                "total_commands_processed": info.get("total_commands_processed") if info else "N/A",
                "keys_count": await self._safe_execute(self.redis_client.dbsize) or 0
            }
        except Exception as e:
            return {
                "connected": self.connected,
                "redis_url": self.redis_url,
                "error": str(e)
            }


# Global Redis manager instance
redis_manager = RedisManager()


# Utility functions for easy access
async def init_redis():
    """Initialize Redis connection"""
    return await redis_manager.initialize()


async def cleanup_redis():
    """Cleanup Redis connection"""
    await redis_manager.close()


# For backward compatibility and easy access
async def get_redis_client():
    """Get Redis client instance"""
    if not redis_manager.connected:
        await redis_manager.initialize()
    return redis_manager.redis_client if redis_manager.connected else None