# test_order.py
import pytest
import websockets
import asyncio
import os

@pytest.mark.asyncio
async def test_websocket_order():
    uri = os.getenv('WEBSOCKET_URI', 'ws://localhost:8000/ws/order')
    async with websockets.connect(uri) as websocket:
        await websocket.send("Test message")
        response = await websocket.recv()
        assert response is not None

