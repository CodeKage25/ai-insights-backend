from pydantic import BaseModel, Field
from typing import List, Any, Optional
from datetime import datetime

class FileUploadResponse(BaseModel):
    file_id: str
    filename: str
    preview: List[List[Any]]
    message: str

class FileStatus(BaseModel):
    file_id: str
    status: str  
    upload_time: datetime
    filename: str