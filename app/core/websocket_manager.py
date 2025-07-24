import json
import logging
from typing import Dict, Set
from fastapi import WebSocket
from datetime import datetime

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        
    async def connect(self, websocket: WebSocket, file_id: str):
        """Connect a WebSocket to a specific file's updates"""
        await websocket.accept()
        
        if file_id not in self.active_connections:
            self.active_connections[file_id] = set()
        
        self.active_connections[file_id].add(websocket)
        logger.info(f"WebSocket connected for file_id: {file_id}")
        
        await self.send_personal_message({
            "type": "connection_established",
            "file_id": file_id,
            "timestamp": datetime.utcnow().isoformat(),
            "message": "Connected to real-time updates"
        }, websocket)
    
    def disconnect(self, websocket: WebSocket, file_id: str):
        """Disconnect a WebSocket"""
        if file_id in self.active_connections:
            self.active_connections[file_id].discard(websocket)
            
            # Clean up empty sets
            if not self.active_connections[file_id]:
                del self.active_connections[file_id]
                
        logger.info(f"WebSocket disconnected for file_id: {file_id}")
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send a message to a specific WebSocket"""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
    
    async def broadcast_to_file(self, file_id: str, message: dict):
        """Broadcast a message to all connections for a specific file"""
        if file_id not in self.active_connections:
            return
            
        # Add timestamp to message
        message["timestamp"] = datetime.utcnow().isoformat()
        
        disconnected_connections = set()
        
        for connection in self.active_connections[file_id]:
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error broadcasting to connection: {e}")
                disconnected_connections.add(connection)
        
        # Clean up disconnected connections
        for connection in disconnected_connections:
            self.active_connections[file_id].discard(connection)
    
    async def send_status_update(self, file_id: str, status: str, message: str = "", progress: float = 0.0, details: dict = None):
        """Send a status update to all connections for a file"""
        update_message = {
            "type": "status_update",
            "file_id": file_id,
            "status": status,
            "message": message,
            "progress": progress,
            "details": details or {}
        }
        
        await self.broadcast_to_file(file_id, update_message)
    
    async def send_insight_progress(self, file_id: str, current_step: str, total_steps: int, current_step_num: int, insights_found: int = 0):
        """Send detailed progress updates during insight generation"""
        progress = (current_step_num / total_steps) * 100
        
        update_message = {
            "type": "insight_progress",
            "file_id": file_id,
            "current_step": current_step,
            "total_steps": total_steps,
            "current_step_num": current_step_num,
            "progress": progress,
            "insights_found": insights_found,
            "message": f"Step {current_step_num}/{total_steps}: {current_step}"
        }
        
        await self.broadcast_to_file(file_id, update_message)
    
    async def send_insights_complete(self, file_id: str, insights_count: int, processing_time: float):
        """Send completion notification with results"""
        completion_message = {
            "type": "insights_complete",
            "file_id": file_id,
            "status": "completed",
            "insights_count": insights_count,
            "processing_time": processing_time,
            "progress": 100.0,
            "message": f"Analysis complete! Found {insights_count} insights in {processing_time:.1f}s"
        }
        
        await self.broadcast_to_file(file_id, completion_message)

manager = ConnectionManager()