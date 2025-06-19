"""
Test WebSocket message flow
"""
import asyncio
import websockets
import json
import aiohttp

async def test_websocket():
    # Start analysis
    async with aiohttp.ClientSession() as session:
        async with session.post(
            'http://localhost:8000/api/analyze',
            json={
                'amazon_url': 'https://www.amazon.com/Tamagotchi-Nano-Peanuts-Silicone-Case/dp/B0FB7FQWJL'
            }
        ) as response:
            data = await response.json()
            session_id = data['session_id']
            print(f"Started analysis with session_id: {session_id}")
    
    # Connect WebSocket
    uri = f"ws://localhost:8000/ws/{session_id}"
    async with websockets.connect(uri) as websocket:
        print(f"Connected to WebSocket")
        
        # Listen for messages
        try:
            while True:
                message = await asyncio.wait_for(websocket.recv(), timeout=30.0)
                data = json.loads(message)
                print(f"\nReceived message:")
                print(f"  Type: {data.get('type')}")
                if data.get('type') == 'agent_progress':
                    progress_data = data.get('data', {})
                    print(f"  Agent: {progress_data.get('agent_name')}")
                    print(f"  Status: {progress_data.get('status')}")
                    print(f"  Progress: {progress_data.get('progress', 0) * 100:.1f}%")
                    print(f"  Task: {progress_data.get('current_task')}")
                    print(f"  Thinking: {progress_data.get('thinking_step')}")
                
                if data.get('type') == 'analysis_complete':
                    print(f"Analysis completed!")
                    break
                    
        except asyncio.TimeoutError:
            print("Timeout waiting for messages")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket())