from pydantic import BaseModel, Field
from typing import List, Optional

class Insight(BaseModel):
    title: str = Field(..., description="Brief title of the insight")
    description: str = Field(..., description="Detailed description of the insight")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score between 0 and 1")
    category: str = Field(..., description="Category of insight (statistical, pattern, anomaly)")
    affected_columns: List[str] = Field(default=[], description="Columns this insight relates to")
    affected_rows: List[int] = Field(default=[], description="Row indices this insight relates to")

class ProcessRequest(BaseModel):
    file_id: str

class InsightResponse(BaseModel):
    file_id: str
    insights: List[Insight]
    processing_time: float
    total_insights: int