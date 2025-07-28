import json
import asyncio
from typing import Dict, Set, Optional
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime


class WebSocketManager:
    """
    WebSocket manager for real-time status updates.
    Manages connections per prompt_id and broadcasts status changes.
    """
    
    def __init__(self):
        # Store active connections by prompt_id
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        
    async def connect(self, websocket: WebSocket, prompt_id: str):
        """Accept a new WebSocket connection for a specific prompt_id"""
        await websocket.accept()
        
        if prompt_id not in self.active_connections:
            self.active_connections[prompt_id] = set()
            
        self.active_connections[prompt_id].add(websocket)
        print(f"📡 WebSocket connected for prompt {prompt_id}. Total connections: {len(self.active_connections[prompt_id])}")
        
    def disconnect(self, websocket: WebSocket, prompt_id: str):
        """Remove a WebSocket connection"""
        if prompt_id in self.active_connections:
            self.active_connections[prompt_id].discard(websocket)
            
            # Clean up empty prompt_id entries
            if not self.active_connections[prompt_id]:
                del self.active_connections[prompt_id]
                
        print(f"📡 WebSocket disconnected for prompt {prompt_id}")
        
    async def send_status_update(self, prompt_id: str, status_data: dict):
        """
        Send status update to all connections for a specific prompt_id
        
        Args:
            prompt_id (str): The prompt ID to send updates for
            status_data (dict): Status data to broadcast
        """
        print(f"📡 WebSocketManager: Attempting to send status update for prompt {prompt_id}")
        print(f"📡 WebSocketManager: Active connections: {list(self.active_connections.keys())}")
        
        if prompt_id not in self.active_connections:
            print(f"📡 WebSocketManager: No active connections for prompt {prompt_id}")
            return
            
        # Add timestamp to status data
        message = {
            "type": "status_update",
            "timestamp": datetime.now().isoformat(),
            "prompt_id": prompt_id,
            "data": status_data
        }
        
        # Get connections for this prompt_id
        connections = self.active_connections[prompt_id].copy()
        
        # Send to all connections, remove failed ones
        failed_connections = set()
        
        for connection in connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                print(f"📡 Failed to send to WebSocket: {e}")
                failed_connections.add(connection)
                
        # Remove failed connections
        for failed_connection in failed_connections:
            self.disconnect(failed_connection, prompt_id)
            
        print(f"📡 Sent status update to {len(connections) - len(failed_connections)} connections for prompt {prompt_id}")
        
    async def send_session_update(self, prompt_id: str, session_data: dict):
        """
        Send session update to all connections for a specific prompt_id
        
        Args:
            prompt_id (str): The prompt ID to send updates for  
            session_data (dict): Session data to broadcast
        """
        print(f"📡 WebSocketManager: Attempting to send session update for prompt {prompt_id}")
        print(f"📡 WebSocketManager: Active connections: {list(self.active_connections.keys())}")
        
        if prompt_id not in self.active_connections:
            print(f"📡 WebSocketManager: No active connections for prompt {prompt_id}")
            return
            
        # Add timestamp to session data
        message = {
            "type": "session_update", 
            "timestamp": datetime.now().isoformat(),
            "prompt_id": prompt_id,
            "data": session_data
        }
        
        # Get connections for this prompt_id
        connections = self.active_connections[prompt_id].copy()
        
        # Send to all connections, remove failed ones
        failed_connections = set()
        
        for connection in connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                print(f"📡 Failed to send to WebSocket: {e}")
                failed_connections.add(connection)
                
        # Remove failed connections
        for failed_connection in failed_connections:
            self.disconnect(failed_connection, prompt_id)
            
        print(f"📡 Sent session update to {len(connections) - len(failed_connections)} connections for prompt {prompt_id}")
        
    def get_connection_count(self, prompt_id: str) -> int:
        """Get number of active connections for a prompt_id"""
        return len(self.active_connections.get(prompt_id, set()))
        
    def get_total_connections(self) -> int:
        """Get total number of active connections across all prompts"""
        return sum(len(connections) for connections in self.active_connections.values())


# Global WebSocket manager instance
websocket_manager = WebSocketManager()
