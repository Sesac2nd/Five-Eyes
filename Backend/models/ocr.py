# models/ocr.py
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, JSON
from sqlalchemy.sql import func
from config.database import Base
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from enum import Enum


class OCRModelType(str, Enum):
    PPOCR = "ppocr"
    AZURE = "azure"


# SQLAlchemy 모델
class OCRLog(Base):
    __tablename__ = "ocr_logs"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), index=True)
    model_type = Column(String(20))  # 'ppocr' 또는 'azure'
    original_filename = Column(String(255))
    file_size = Column(Integer)  # bytes
    processing_time = Column(Float)  # seconds
    success = Column(Boolean)
    error_message = Column(Text, nullable=True)
    confidence_avg = Column(Float, nullable=True)
    word_count = Column(Integer, nullable=True)
    result_data = Column(JSON, nullable=True)  # OCR 결과 전체
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "session_id": self.session_id,
            "model_type": self.model_type,
            "original_filename": self.original_filename,
            "file_size": self.file_size,
            "processing_time": self.processing_time,
            "success": self.success,
            "error_message": self.error_message,
            "confidence_avg": self.confidence_avg,
            "word_count": self.word_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# Pydantic 모델 (API 요청/응답)
class OCRRequest(BaseModel):
    model_type: OCRModelType
    session_id: Optional[str] = None


class WordResult(BaseModel):
    text: str
    confidence: float
    bbox: List[int]  # [x, y, width, height]
    polygon: Optional[List[float]] = None  # [x1, y1, x2, y2, ...]


class LineResult(BaseModel):
    line_number: int
    words: List[WordResult]
    full_text: str
    avg_confidence: float
    bbox: List[int]  # 전체 라인의 바운딩 박스


class OCRResult(BaseModel):
    success: bool
    model_type: str
    processing_time: float
    confidence_avg: Optional[float] = None
    word_count: Optional[int] = None
    lines: Optional[List[LineResult]] = None
    full_text: Optional[str] = None
    error_message: Optional[str] = None


class OCRResponse(BaseModel):
    log_id: int
    session_id: str
    result: OCRResult
