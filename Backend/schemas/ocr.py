from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime


class TextBlock(BaseModel):
    """텍스트 블록 정보"""

    text: str = Field(..., description="인식된 텍스트")
    confidence: float = Field(..., description="신뢰도 (0.0-1.0)")
    coordinates: Dict[str, Any] = Field(..., description="좌표 정보")


class ClassicalChineseBlock(BaseModel):
    """한문 블록 정보"""

    original_text: str = Field(..., description="원본 텍스트")
    classical_chinese: str = Field(..., description="추출된 한문")
    confidence: float = Field(..., description="신뢰도")
    coordinates: Dict[str, Any] = Field(..., description="좌표 정보")
    char_count: int = Field(..., description="한자 개수")


class HanjaBlock(BaseModel):
    """한자 블록 정보"""

    original_text: str = Field(..., description="원본 텍스트")
    hanja_text: str = Field(..., description="추출된 한자")
    confidence: float = Field(..., description="신뢰도")
    coordinates: Dict[str, Any] = Field(..., description="좌표 정보")
    hanja_count: int = Field(..., description="한자 개수")
    language: Optional[str] = Field(None, description="인식된 언어")


class OCRResponse(BaseModel):
    """OCR 응답"""

    success: bool = Field(..., description="성공 여부")
    message: str = Field(..., description="응답 메시지")
    text_blocks: List[TextBlock] = Field(default=[], description="인식된 텍스트 블록들")
    full_text: str = Field(default="", description="전체 텍스트")
    total_blocks: int = Field(default=0, description="총 블록 수")
    average_confidence: float = Field(default=0.0, description="평균 신뢰도")
    classical_chinese: Optional[Dict[str, Any]] = Field(
        None, description="한문 추출 결과"
    )
    service_used: str = Field(..., description="사용된 서비스")
    language: Optional[str] = Field(None, description="인식된 언어")
    orientation: Optional[str] = Field(None, description="텍스트 방향")
    text_angle: Optional[float] = Field(None, description="텍스트 각도")
    processing_time: Optional[float] = Field(None, description="처리 시간 (초)")


class OCRComparisonResponse(BaseModel):
    """OCR 비교 응답"""

    success: bool = Field(..., description="성공 여부")
    message: str = Field(..., description="응답 메시지")
    ppocr_result: Dict[str, Any] = Field(..., description="PPOCR 결과")
    azure_result: Dict[str, Any] = Field(..., description="Azure OCR 결과")
    comparison: Dict[str, Any] = Field(..., description="비교 결과")
    recommendation: str = Field(..., description="추천사항")


class HanjaExtractionResponse(BaseModel):
    """한자 추출 응답"""

    success: bool = Field(..., description="성공 여부")
    message: str = Field(..., description="응답 메시지")
    extracted_hanja: Dict[str, Any] = Field(..., description="추출된 한자 정보")
    unique_hanja_chars: List[str] = Field(default=[], description="고유 한자 목록")
    total_unique_chars: int = Field(default=0, description="총 고유 한자 수")
    extraction_method: str = Field(..., description="추출 방법")


class OCRServiceInfo(BaseModel):
    """OCR 서비스 정보"""

    ppocr_service: Dict[str, Any] = Field(..., description="PPOCR 서비스 정보")
    azure_service: Dict[str, Any] = Field(..., description="Azure 서비스 정보")
    available_services: List[str] = Field(..., description="사용 가능한 서비스 목록")
    supported_formats: List[str] = Field(..., description="지원 파일 형식")
    max_file_size: str = Field(..., description="최대 파일 크기")


class BatchOCRRequest(BaseModel):
    """배치 OCR 요청"""

    method: str = Field(default="ppocr", description="사용할 OCR 방법")
    preprocess: bool = Field(default=True, description="전처리 여부")
    azure_language: str = Field(default="zh-Hans", description="Azure OCR 언어 설정")


class BatchOCRResponse(BaseModel):
    """배치 OCR 응답"""

    success: bool = Field(..., description="성공 여부")
    message: str = Field(..., description="응답 메시지")
    results: List[Dict[str, Any]] = Field(..., description="각 파일별 처리 결과")
    statistics: Dict[str, Any] = Field(..., description="처리 통계")


# 역사 문서 관련 스키마
class HistoricalDocumentOCR(BaseModel):
    """역사 문서 OCR 결과"""

    document_id: Optional[str] = Field(None, description="문서 ID")
    document_title: str = Field(..., description="문서 제목")
    page_number: Optional[int] = Field(None, description="페이지 번호")
    ocr_result: OCRResponse = Field(..., description="OCR 결과")
    classical_chinese_analysis: Optional[Dict[str, Any]] = Field(
        None, description="한문 분석 결과"
    )
    historical_period: Optional[str] = Field(None, description="역사 시대")
    processed_at: datetime = Field(
        default_factory=datetime.now, description="처리 시간"
    )


class SillokPageOCR(BaseModel):
    """조선왕조실록 페이지 OCR"""

    reign_name: str = Field(..., description="왕명")
    volume: int = Field(..., description="권수")
    page: int = Field(..., description="페이지")
    year: Optional[int] = Field(None, description="연도")
    month: Optional[int] = Field(None, description="월")
    day: Optional[int] = Field(None, description="일")
    original_text: str = Field(..., description="원문")
    translated_text: Optional[str] = Field(None, description="번역문")
    ocr_confidence: float = Field(..., description="OCR 신뢰도")
    verification_status: str = Field(default="pending", description="검증 상태")


# 고급 분석 스키마
class TextAnalysisResult(BaseModel):
    """텍스트 분석 결과"""

    character_count: int = Field(..., description="총 문자 수")
    hanja_count: int = Field(..., description="한자 수")
    korean_count: int = Field(default=0, description="한글 수")
    punctuation_count: int = Field(default=0, description="구두점 수")
    unique_characters: List[str] = Field(default=[], description="고유 문자 목록")
    difficulty_level: str = Field(..., description="난이도 수준")


class DocumentClassification(BaseModel):
    """문서 분류 결과"""

    document_type: str = Field(..., description="문서 유형")
    historical_period: str = Field(..., description="역사 시대")
    confidence: float = Field(..., description="분류 신뢰도")
    keywords: List[str] = Field(default=[], description="주요 키워드")


class OCRQualityAssessment(BaseModel):
    """OCR 품질 평가"""

    overall_quality: str = Field(..., description="전체 품질 등급")
    clarity_score: float = Field(..., description="명확도 점수")
    completeness_score: float = Field(..., description="완성도 점수")
    accuracy_estimation: float = Field(..., description="정확도 추정")
    improvement_suggestions: List[str] = Field(default=[], description="개선 제안사항")
