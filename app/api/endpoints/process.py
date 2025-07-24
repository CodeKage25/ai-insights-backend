from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.insight import ProcessRequest
from app.services.file_service import FileService
from app.services.insight_service import InsightService

router = APIRouter()

@router.post("/process", response_model=dict)
async def process_file(
    request: ProcessRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Start processing a file to generate insights with WebSocket updates"""
    try:
        # Validate file_id exists
        FileService.get_file_record(request.file_id, db)  
        FileService.update_processing_status(request.file_id, "processing", db)

        # Start background task for processing insights
        background_tasks.add_task(
            InsightService.generate_insights_with_progress,
            request.file_id
        )

        return {
            "message": "Processing started with real-time updates",
            "file_id": request.file_id,
            "status": "processing",
            "websocket_url": f"/api/v1/ws/{request.file_id}"
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")
