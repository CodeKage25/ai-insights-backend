import os
import uuid
from typing import List, Any, Tuple
from sqlalchemy.orm import Session
from fastapi import UploadFile
import logging

from app.core.database import FileRecord, get_db
from app.core.config import get_settings
from app.utils.file_parser import parse_file, FileParseError
from app.utils.validators import validate_file_extension, validate_file_size
from sqlalchemy.orm import Session


logger = logging.getLogger(__name__)
settings = get_settings()

class FileService:
    @staticmethod
    async def save_uploaded_file(
        file: UploadFile, 
        db: Session
    ) -> Tuple[str, List[List[Any]]]:
        """Save uploaded file and return file_id and preview data"""
        
        # Validate file extension
        if not validate_file_extension(file.filename, settings.allowed_extensions):
            raise ValueError(f"Unsupported file type. Allowed: {settings.allowed_extensions}")
        
        # Read file content
        content = await file.read()
        file_size = len(content)
        
        # Validate file size
        if not validate_file_size(file_size, settings.max_file_size):
            raise ValueError(f"File too large. Max size: {settings.max_file_size} bytes")
        
        # Generate unique file ID and path
        file_id = str(uuid.uuid4())
        file_extension = os.path.splitext(file.filename)[1]
        filepath = os.path.join(settings.upload_dir, f"{file_id}{file_extension}")
        
        try:
            # Save file to disk
            with open(filepath, "wb") as f:
                f.write(content)
            
            # Parse file for preview
            preview_data, _ = parse_file(filepath, settings.max_preview_rows)
            
            # Save record to database
            file_record = FileRecord(
                id=file_id,
                filename=file.filename,
                filepath=filepath,
                file_size=file_size,
                preview_data=preview_data,
                processing_status="uploaded"
            )
            db.add(file_record)
            db.commit()
            
            logger.info(f"File uploaded successfully: {file_id}")
            return file_id, preview_data
            
        except FileParseError as e:
            # Clean up file if parsing failed
            if os.path.exists(filepath):
                os.remove(filepath)
            raise ValueError(f"File parsing error: {str(e)}")
        except Exception as e:
            # Clean up file if database save failed
            if os.path.exists(filepath):
                os.remove(filepath)
            logger.error(f"Error saving file: {str(e)}")
            raise ValueError(f"Failed to save file: {str(e)}")
    
    @staticmethod
    def get_file_record(file_id: str, db: Session) -> FileRecord:
        """Get file record from database"""
        record = db.query(FileRecord).filter(FileRecord.id == file_id).first()
        if not record:
            raise ValueError(f"File not found: {file_id}")
        return record
    
    @staticmethod
    def update_processing_status(file_id: str, status: str, db: Session):
        """Update processing status"""
        record = FileService.get_file_record(file_id, db)
        record.processing_status = status
        db.commit()