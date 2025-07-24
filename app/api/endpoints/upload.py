from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.file import FileUploadResponse
from app.services.file_service import FileService

router = APIRouter()

@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload a CSV or Excel file and return preview data"""
    try:
        file_id, preview_data = await FileService.save_uploaded_file(file, db)
        
        return FileUploadResponse(
            file_id=file_id,
            filename=file.filename,
            preview=preview_data,
            message="File uploaded successfully"
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")