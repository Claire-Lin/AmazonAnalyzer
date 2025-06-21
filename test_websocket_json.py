#!/usr/bin/env python3
"""
Test script to verify WebSocket JSON messages
"""
import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://localhost:8000/ws/test-session-123"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected to WebSocket")
            
            # Wait for messages
            for i in range(10):
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    print(f"\nMessage {i+1}:")
                    print(f"Raw data: {repr(message)}")
                    print(f"Length: {len(message)}")
                    
                    # Try to parse as JSON
                    try:
                        parsed = json.loads(message)
                        print(f"Parsed successfully: {parsed.get('type', 'no type')}")
                    except json.JSONDecodeError as e:
                        print(f"JSON parse error: {e}")
                        print(f"Error position: {e.pos}")
                        print(f"Data around error: {message[max(0, e.pos-50):e.pos+50]}")
                        
                except asyncio.TimeoutError:
                    print("No message received in 5 seconds")
                    break
                    
    except Exception as e:
        print(f"Connection error: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket())