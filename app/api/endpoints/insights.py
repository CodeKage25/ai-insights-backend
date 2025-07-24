from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.models.insight import InsightResponse, Insight
from app.models.file import FileStatus
from app.services.file_service import FileService

router = APIRouter()

@router.get("/insights")
async def get_insights(
    file_id: str = Query(..., description="File ID to get insights for"),
    db: Session = Depends(get_db)
):
    """Get generated insights for a file"""
    try:
        file_record = FileService.get_file_record(file_id, db)
        
        if file_record.processing_status == "uploaded":
            return {"message": "File not yet processed", "status": "uploaded"}
        elif file_record.processing_status == "processing":
            return {"message": "Processing in progress", "status": "processing"}
        elif file_record.processing_status == "failed":
            return {"message": "Processing failed", "status": "failed"}
        elif file_record.processing_status == "completed":
            if file_record.insights:
                insights = [Insight(**insight) for insight in file_record.insights]
                return InsightResponse(
                    file_id=file_id,
                    insights=insights,
                    processing_time=0.0,  
                    total_insights=len(insights)
                )
            else:
                return {"message": "No insights generated", "status": "completed"}
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/status")
async def get_file_status(
    file_id: str = Query(..., description="File ID to check status"),
    db: Session = Depends(get_db)
):
    """Get processing status for a file"""
    try:
        file_record = FileService.get_file_record(file_id, db)
        
        return FileStatus(
            file_id=file_id,
            status=file_record.processing_status,
            upload_time=file_record.upload_time,
            filename=file_record.filename
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")