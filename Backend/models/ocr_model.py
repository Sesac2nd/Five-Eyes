from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float
from sqlalchemy.sql import func
from config.database import Base


class OCRAnalysis(Base):
    __tablename__ = "ocr_analyses"

    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(String(100), index=True, unique=True)  # UUID for analysis
    filename = Column(String(255))  # Original filename
    engine = Column(String(20))  # 'paddle' or 'azure'
    status = Column(String(20), default="processing")  # 'processing', 'completed', 'failed'
    extracted_text = Column(Text, nullable=True)  # Extracted OCR text
    word_count = Column(Integer, default=0)  # Number of words extracted
    confidence_score = Column(Float, default=0.0)  # Average confidence score
    processing_time = Column(Float, default=0.0)  # Processing time in seconds
    extract_text_only = Column(Boolean, default=False)  # Text-only extraction flag
    visualization_requested = Column(Boolean, default=True)  # Visualization request flag
    visualization_path = Column(String(500), nullable=True)  # Path to visualization file
    error_message = Column(Text, nullable=True)  # Error message if failed
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "analysis_id": self.analysis_id,
            "filename": self.filename,
            "engine": self.engine,
            "status": self.status,
            "extracted_text": self.extracted_text,
            "word_count": self.word_count,
            "confidence_score": self.confidence_score,
            "processing_time": self.processing_time,
            "extract_text_only": self.extract_text_only,
            "visualization_requested": self.visualization_requested,
            "visualization_path": self.visualization_path,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }