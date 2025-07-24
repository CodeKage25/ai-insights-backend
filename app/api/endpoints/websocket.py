from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy.orm import Session
import logging

from app.core.database import get_db
from app.core.websocket_manager import manager
from app.services.file_service import FileService

logger = logging.getLogger(__name__)
router = APIRouter()

@router.websocket("/ws/{file_id}")
async def websocket_endpoint(
    websocket: WebSocket, 
    file_id: str,
    db: Session = Depends(get_db)
):
    """WebSocket endpoint for real-time file processing updates"""
    try:
        # Verify file exists before accepting connection
        try:
            FileService.get_file_record(file_id, db)
        except ValueError:
            await websocket.close(code=4004, reason="File not found")
            return
        
        # Accept the connection
        await manager.connect(websocket, file_id)
        
        try:
            # Keep connection alive and handle incoming messages
            while True:
                # Wait for client messages (ping/pong, etc.)
                data = await websocket.receive_text()
                
                # Handle client messages if needed
                try:
                    import json
                    message = json.loads(data)
                    
                    if message.get("type") == "ping":
                        await manager.send_personal_message({
                            "type": "pong",
                            "file_id": file_id
                        }, websocket)
                        
                except json.JSONDecodeError:
                    pass
                    
        except WebSocketDisconnect:
            manager.disconnect(websocket, file_id)
            logger.info(f"WebSocket disconnected for file {file_id}")
            
    except Exception as e:
        logger.error(f"WebSocket error for file {file_id}: {e}")
        await websocket.close(code=1011, reason="Internal server error")