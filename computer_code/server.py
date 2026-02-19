#!/usr/bin/env python3
"""
Websocket server to receive touch sensor data from ESP32.
Saves received CSV data to a file.

Install requirements: pip install websockets
Then run: python server.py
"""

import asyncio
import websockets
import os
from datetime import datetime

# Configuration
HOST = "0.0.0.0"  # Listen on all interfaces
PORT = 8765
DATA_FOLDER = "./received_data"

# Create data folder if it doesn't exist
os.makedirs(DATA_FOLDER, exist_ok=True)


async def handle_client(websocket, path):
    """Handle incoming websocket connection from ESP32."""
    remote_addr = websocket.remote_address
    print(f"[{datetime.now()}] Client connected: {remote_addr}")
    
    try:
        async for message in websocket:
            # message should contain the CSV data
            if isinstance(message, bytes):
                message = message.decode('utf-8')
            
            print(f"[{datetime.now()}] Received {len(message)} bytes from {remote_addr}")
            
            # Save to file with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{DATA_FOLDER}/touch_log_{timestamp}.csv"
            
            with open(filename, 'w') as f:
                f.write(message)
            
            print(f"[{datetime.now()}] Data saved to {filename}")
            
            # Send acknowledgment
            await websocket.send("OK")
            
    except websockets.exceptions.ConnectionClosed:
        print(f"[{datetime.now()}] Client disconnected: {remote_addr}")
    except Exception as e:
        print(f"[{datetime.now()}] ERROR: {e}")


async def main():
    """Start the websocket server."""
    print(f"Starting WebSocket server on ws://{HOST}:{PORT}")
    print(f"Data will be saved to: {os.path.abspath(DATA_FOLDER)}")
    
    async with websockets.serve(handle_client, HOST, PORT):
        print("Server is running. Waiting for connections...")
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    asyncio.run(main())
