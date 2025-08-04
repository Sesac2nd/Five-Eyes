from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime


class TTSRequest(BaseModel):
    """TTS 요청"""

    text: str = Field(..., description="변환할 텍스트", max_length=1000)
    voice_name: str = Field(
        default="ko-KR-HyunsuMultilingualNeural", description="사용할 음성"
    )
    output_format: str = Field(default="wav", description="출력 오디오 형식")


class TTSResponse(BaseModel):
    """TTS 응답"""

    success: bool = Field(..., description="성공 여부")
    message: str = Field(..., description="응답 메시지")
    audio_data: Optional[str] = Field(None, description="Base64 인코딩된 오디오 데이터")
    audio_size: int = Field(default=0, description="오디오 파일 크기 (bytes)")
    voice_name: str = Field(..., description="사용된 음성")
    text: str = Field(..., description="변환된 텍스트")
    output_format: str = Field(default="wav", description="출력 형식")
    processing_time: Optional[float] = Field(None, description="처리 시간 (초)")
    ssml_used: bool = Field(default=False, description="SSML 사용 여부")


class STTRequest(BaseModel):
    """STT 요청"""

    language: str = Field(default="ko-KR", description="인식할 언어")
    audio_format: str = Field(default="wav", description="오디오 형식")


class STTResponse(BaseModel):
    """STT 응답"""

    success: bool = Field(..., description="성공 여부")
    message: str = Field(..., description="응답 메시지")
    recognized_text: str = Field(default="", description="인식된 텍스트")
    confidence: float = Field(default=0.0, description="인식 신뢰도 (0.0-1.0)")
    language: str = Field(..., description="인식된 언어")
    audio_duration: float = Field(default=0.0, description="오디오 길이 (초)")
    file_size: int = Field(default=0, description="파일 크기 (bytes)")
    processing_time: Optional[float] = Field(None, description="처리 시간 (초)")


class SSMLRequest(BaseModel):
    """SSML TTS 요청"""

    text: str = Field(..., description="변환할 텍스트", max_length=1000)
    voice_name: str = Field(
        default="ko-KR-HyunsuMultilingualNeural", description="사용할 음성"
    )
    rate: str = Field(default="medium", description="말하기 속도 (slow, medium, fast)")
    pitch: str = Field(default="medium", description="음높이 (low, medium, high)")


class Voice(BaseModel):
    """음성 정보"""

    name: str = Field(..., description="음성 이름")
    gender: str = Field(..., description="성별")
    description: str = Field(..., description="음성 설명")
    recommended: bool = Field(default=False, description="추천 여부")


class VoiceInfo(BaseModel):
    """음성 정보 응답"""

    language: str = Field(..., description="언어")
    voices: List[Voice] = Field(..., description="사용 가능한 음성 목록")
    default_voice: str = Field(..., description="기본 음성")
    total_voices: int = Field(..., description="총 음성 수")


class SpeechServiceInfo(BaseModel):
    """음성 서비스 정보"""

    service_name: str = Field(..., description="서비스 이름")
    enabled: bool = Field(..., description="서비스 활성화 여부")
    region: str = Field(..., description="Azure 리전")
    features: List[str] = Field(..., description="지원 기능")
    supported_languages: List[str] = Field(..., description="지원 언어")
    audio_formats: List[str] = Field(..., description="지원 오디오 형식")
    tts_voices_count: int = Field(..., description="TTS 음성 수")
    max_text_length: int = Field(..., description="최대 텍스트 길이")
    max_audio_duration: int = Field(..., description="최대 오디오 길이 (초)")


# 역사 텍스트 특화 스키마
class HistoricalReadingRequest(BaseModel):
    """역사 텍스트 읽기 요청"""

    text: str = Field(..., description="읽을 역사 텍스트")
    voice_name: str = Field(
        default="ko-KR-HyunsuMultilingualNeural", description="사용할 음성"
    )
    reading_style: str = Field(
        default="formal", description="읽기 스타일 (formal, narrative, explanatory)"
    )


class HistoricalReadingResponse(BaseModel):
    """역사 텍스트 읽기 응답"""

    success: bool = Field(..., description="성공 여부")
    message: str = Field(..., description="응답 메시지")
    audio_data: str = Field(..., description="Base64 인코딩된 오디오 데이터")
    audio_size: int = Field(..., description="오디오 파일 크기")
    reading_style: str = Field(..., description="사용된 읽기 스타일")
    processed_text: str = Field(..., description="전처리된 텍스트")
    original_text: str = Field(..., description="원본 텍스트")


class VoiceMemoRequest(BaseModel):
    """음성 메모 요청"""

    memo_title: str = Field(..., description="메모 제목")
    category: str = Field(default="general", description="메모 카테고리")


class VoiceMemo(BaseModel):
    """음성 메모"""

    id: Optional[str] = Field(None, description="메모 ID")
    title: str = Field(..., description="메모 제목")
    category: str = Field(..., description="메모 카테고리")
    transcribed_text: str = Field(..., description="변환된 텍스트")
    confidence: float = Field(..., description="변환 신뢰도")
    duration: float = Field(..., description="오디오 길이")
    original_audio_size: int = Field(..., description="원본 오디오 크기")
    created_by: int = Field(..., description="생성자 ID")
    created_at: datetime = Field(..., description="생성 시간")


class VoiceMemoResponse(BaseModel):
    """음성 메모 응답"""

    success: bool = Field(..., description="성공 여부")
    message: str = Field(..., description="응답 메시지")
    memo: VoiceMemo = Field(..., description="생성된 메모")
    suggestions: List[str] = Field(default=[], description="추천 작업")


# 고급 음성 처리 스키마
class AudioAnalysis(BaseModel):
    """오디오 분석 결과"""

    duration: float = Field(..., description="오디오 길이 (초)")
    sample_rate: int = Field(..., description="샘플링 레이트")
    channels: int = Field(..., description="채널 수")
    bit_depth: int = Field(..., description="비트 깊이")
    format: str = Field(..., description="오디오 형식")
    quality_score: float = Field(..., description="음질 점수 (0.0-1.0)")


class SpeechQualityAssessment(BaseModel):
    """음성 품질 평가"""

    clarity: float = Field(..., description="명료도 (0.0-1.0)")
    volume_level: str = Field(..., description="음량 수준 (low, medium, high)")
    background_noise: str = Field(
        ..., description="배경 소음 수준 (none, low, medium, high)"
    )
    speech_rate: str = Field(..., description="말하기 속도 (slow, normal, fast)")
    overall_quality: str = Field(
        ..., description="전체 품질 (poor, fair, good, excellent)"
    )
    recommendations: List[str] = Field(default=[], description="개선 권장사항")


class BatchSpeechRequest(BaseModel):
    """배치 음성 처리 요청"""

    operation: str = Field(..., description="처리 작업 (tts, stt)")
    language: str = Field(default="ko-KR", description="언어 설정")
    voice_name: Optional[str] = Field(None, description="TTS 음성 (TTS 전용)")


class BatchSpeechResponse(BaseModel):
    """배치 음성 처리 응답"""

    success: bool = Field(..., description="성공 여부")
    message: str = Field(..., description="응답 메시지")
    results: List[Dict[str, Any]] = Field(..., description="각 파일별 처리 결과")
    statistics: Dict[str, Any] = Field(..., description="처리 통계")
    total_processing_time: float = Field(..., description="총 처리 시간 (초)")


# 실시간 음성 처리 스키마
class RealTimeSpeechSession(BaseModel):
    """실시간 음성 세션"""

    session_id: str = Field(..., description="세션 ID")
    language: str = Field(default="ko-KR", description="인식 언어")
    status: str = Field(..., description="세션 상태 (active, paused, ended)")
    start_time: datetime = Field(..., description="시작 시간")
    duration: float = Field(default=0.0, description="진행 시간 (초)")
    transcript: str = Field(default="", description="현재까지 인식된 텍스트")


class RealTimeSpeechResponse(BaseModel):
    """실시간 음성 응답"""

    session_id: str = Field(..., description="세션 ID")
    partial_text: str = Field(default="", description="부분 인식 텍스트")
    final_text: str = Field(default="", description="최종 인식 텍스트")
    confidence: float = Field(default=0.0, description="인식 신뢰도")
    is_final: bool = Field(default=False, description="최종 결과 여부")
    timestamp: datetime = Field(default_factory=datetime.now, description="응답 시간")
