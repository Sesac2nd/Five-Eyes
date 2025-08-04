from fastapi import APIRouter, File, UploadFile, HTTPException, Form
from fastapi.responses import JSONResponse
from typing import Optional
import logging

from services.speech_service import speech_service
from schemas.speech import (
    TTSRequest,
    TTSResponse,
    STTRequest,
    STTResponse,
    VoiceInfo,
    SpeechServiceInfo,
    SSMLRequest,
)
from utils.file_handler import validate_audio_file

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/tts", response_model=TTSResponse)
async def text_to_speech(
    text: str = Form(...),
    voice_name: str = Form("ko-KR-HyunsuMultilingualNeural"),
    output_format: str = Form("wav"),
):
    """텍스트를 음성으로 변환"""
    try:
        if not text or len(text.strip()) == 0:
            raise HTTPException(status_code=400, detail="텍스트가 비어있습니다.")

        if len(text) > 1000:
            raise HTTPException(
                status_code=400, detail="텍스트가 너무 깁니다. (최대 1000자)"
            )

        logger.info(f"🔊 TTS 요청: '{text[:50]}...' (음성: {voice_name})")

        # TTS 수행
        result = speech_service.text_to_speech(text.strip(), voice_name, output_format)

        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["error"])

        return TTSResponse(
            success=True,
            message="음성 합성 완료",
            audio_data=result["audio_data"],
            audio_size=result["audio_size"],
            voice_name=voice_name,
            text=text,
            output_format=output_format,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ TTS 처리 오류: {e}")
        raise HTTPException(
            status_code=500, detail=f"음성 합성 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/tts-json", response_model=TTSResponse)
async def text_to_speech_json(request: TTSRequest):
    """텍스트를 음성으로 변환 (JSON 방식)"""
    try:
        if not request.text or len(request.text.strip()) == 0:
            raise HTTPException(status_code=400, detail="텍스트가 비어있습니다.")

        if len(request.text) > 1000:
            raise HTTPException(
                status_code=400, detail="텍스트가 너무 깁니다. (최대 1000자)"
            )

        logger.info(
            f"🔊 TTS JSON 요청: '{request.text[:50]}...' (음성: {request.voice_name})"
        )

        # TTS 수행
        result = speech_service.text_to_speech(
            request.text.strip(), request.voice_name, request.output_format
        )

        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["error"])

        return TTSResponse(
            success=True,
            message="음성 합성 완료",
            audio_data=result["audio_data"],
            audio_size=result["audio_size"],
            voice_name=request.voice_name,
            text=request.text,
            output_format=request.output_format,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ TTS JSON 처리 오류: {e}")
        raise HTTPException(
            status_code=500, detail=f"음성 합성 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/stt", response_model=STTResponse)
async def speech_to_text(
    file: UploadFile = File(...),
    language: str = Form("ko-KR"),
    audio_format: str = Form("wav"),
):
    """음성을 텍스트로 변환"""
    try:
        # 파일 검증
        if not validate_audio_file(file):
            raise HTTPException(
                status_code=400, detail="지원하지 않는 오디오 형식입니다."
            )

        # 파일 읽기
        audio_bytes = await file.read()

        if len(audio_bytes) == 0:
            raise HTTPException(status_code=400, detail="빈 오디오 파일입니다.")

        logger.info(
            f"🎤 STT 요청: {file.filename} ({len(audio_bytes)} bytes, 언어: {language})"
        )

        # STT 수행
        result = speech_service.speech_to_text(audio_bytes, language, audio_format)

        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["error"])

        return STTResponse(
            success=True,
            message="음성 인식 완료",
            recognized_text=result["recognized_text"],
            confidence=result["confidence"],
            language=language,
            audio_duration=result.get("audio_duration", 0),
            file_size=len(audio_bytes),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ STT 처리 오류: {e}")
        raise HTTPException(
            status_code=500, detail=f"음성 인식 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/tts-ssml", response_model=TTSResponse)
async def text_to_speech_with_ssml(request: SSMLRequest):
    """SSML을 사용한 고급 음성 합성"""
    try:
        if not request.text or len(request.text.strip()) == 0:
            raise HTTPException(status_code=400, detail="텍스트가 비어있습니다.")

        logger.info(
            f"🎵 SSML TTS 요청: '{request.text[:50]}...' (음성: {request.voice_name})"
        )

        # SSML 생성
        ssml = speech_service.create_ssml(
            request.text, request.voice_name, request.rate, request.pitch
        )

        # SSML TTS 수행
        result = speech_service.text_to_speech_with_ssml(ssml)

        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["error"])

        return TTSResponse(
            success=True,
            message="SSML 음성 합성 완료",
            audio_data=result["audio_data"],
            audio_size=result["audio_size"],
            voice_name=request.voice_name,
            text=request.text,
            output_format="wav",
            ssml_used=True,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ SSML TTS 처리 오류: {e}")
        raise HTTPException(
            status_code=500, detail=f"SSML 음성 합성 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/voices", response_model=VoiceInfo)
async def get_available_voices(language: str = "ko-KR"):
    """사용 가능한 음성 목록 조회"""
    try:
        voices_info = speech_service.get_available_voices(language)

        return VoiceInfo(
            language=voices_info["language"],
            voices=voices_info["voices"],
            default_voice=voices_info["default"],
            total_voices=len(voices_info["voices"]),
        )

    except Exception as e:
        logger.error(f"❌ 음성 목록 조회 오류: {e}")
        raise HTTPException(
            status_code=500, detail="음성 목록 조회 중 오류가 발생했습니다."
        )


@router.post("/historical-reading")
async def historical_text_reading(
    text: str = Form(...),
    voice_name: str = Form("ko-KR-HyunsuMultilingualNeural"),
    reading_style: str = Form("formal"),  # formal, narrative, explanatory
):
    """역사 텍스트 전용 음성 읽기"""
    try:
        # 역사 텍스트 특화 전처리
        processed_text = _preprocess_historical_text(text, reading_style)

        # 읽기 스타일에 따른 SSML 설정
        rate = "slow" if reading_style == "formal" else "medium"
        pitch = "low" if reading_style == "formal" else "medium"

        # SSML 생성
        ssml = speech_service.create_ssml(processed_text, voice_name, rate, pitch)

        # 음성 합성
        result = speech_service.text_to_speech_with_ssml(ssml)

        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["error"])

        return {
            "success": True,
            "message": f"역사 텍스트 읽기 완료 ({reading_style} 스타일)",
            "audio_data": result["audio_data"],
            "audio_size": result["audio_size"],
            "reading_style": reading_style,
            "processed_text": processed_text,
            "original_text": text,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 역사 텍스트 읽기 오류: {e}")
        raise HTTPException(
            status_code=500, detail=f"역사 텍스트 읽기 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/voice-memo")
async def create_voice_memo(
    file: UploadFile = File(...),
    memo_title: str = Form(...),
    category: str = Form("general"),  # research, notes, ideas, general
):
    """음성 메모 생성 및 텍스트 변환"""
    try:
        # 파일 검증
        if not validate_audio_file(file):
            raise HTTPException(
                status_code=400, detail="지원하지 않는 오디오 형식입니다."
            )

        # 파일 읽기
        audio_bytes = await file.read()

        if len(audio_bytes) == 0:
            raise HTTPException(status_code=400, detail="빈 오디오 파일입니다.")

        logger.info(f"📝 음성 메모 생성: {memo_title} ({category})")

        # STT 수행
        stt_result = speech_service.speech_to_text(audio_bytes, "ko-KR", "wav")

        if not stt_result["success"]:
            raise HTTPException(status_code=500, detail=stt_result["error"])

        # 메모 데이터 (실제로는 데이터베이스에 저장하지 않고 응답만 반환)
        memo_data = {
            "title": memo_title,
            "category": category,
            "original_audio_size": len(audio_bytes),
            "transcribed_text": stt_result["recognized_text"],
            "confidence": stt_result["confidence"],
            "duration": stt_result.get("audio_duration", 0),
            "created_at": "2024-01-01T00:00:00Z",  # 현재 시간으로 대체 가능
        }

        return {
            "success": True,
            "message": "음성 메모 생성 완료",
            "memo": memo_data,
            "suggestions": _generate_memo_suggestions(
                stt_result["recognized_text"], category
            ),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 음성 메모 생성 오류: {e}")
        raise HTTPException(
            status_code=500, detail=f"음성 메모 생성 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/service-info", response_model=SpeechServiceInfo)
async def get_speech_service_info():
    """음성 서비스 정보 조회"""
    try:
        service_info = speech_service.get_service_info()

        return SpeechServiceInfo(
            service_name=service_info["service_name"],
            enabled=service_info["enabled"],
            region=service_info["region"],
            features=service_info["features"],
            supported_languages=service_info["supported_languages"],
            audio_formats=service_info["audio_formats"],
            tts_voices_count=len(
                speech_service.get_available_voices("ko-KR")["voices"]
            ),
            max_text_length=1000,
            max_audio_duration=60,
        )

    except Exception as e:
        logger.error(f"❌ 음성 서비스 정보 조회 오류: {e}")
        raise HTTPException(
            status_code=500, detail="음성 서비스 정보 조회 중 오류가 발생했습니다."
        )


@router.get("/health")
async def speech_health_check():
    """음성 서비스 상태 확인"""
    return {
        "status": "healthy",
        "service_enabled": speech_service.enabled,
        "capabilities": [
            "텍스트 음성 변환 (TTS)",
            "음성 텍스트 변환 (STT)",
            "SSML 지원",
            "다국어 지원",
            "역사 텍스트 특화 읽기",
        ],
        "authentication": "disabled",
    }


# 유틸리티 함수들
def _preprocess_historical_text(text: str, reading_style: str) -> str:
    """역사 텍스트 전처리"""
    processed = text.strip()

    # 한문 문장부호 처리
    processed = processed.replace("。", ". ")
    processed = processed.replace("，", ", ")
    processed = processed.replace("、", ", ")

    # 읽기 스타일에 따른 처리
    if reading_style == "formal":
        # 공식적인 읽기: 구두점 강화
        processed = processed.replace(".", "... ")
        processed = processed.replace(",", ", ")
    elif reading_style == "narrative":
        # 서술적 읽기: 자연스러운 흐름
        processed = processed.replace(".", ". ")
    elif reading_style == "explanatory":
        # 설명적 읽기: 명확한 구분
        processed = processed.replace(".", "입니다. ")
        processed = processed.replace("다.", "다는 것입니다.")

    return processed


def _generate_memo_suggestions(text: str, category: str) -> list:
    """메모 제안사항 생성"""
    suggestions = []

    if category == "research":
        suggestions.extend(
            ["관련 사료 검색해보기", "참고문헌 정리하기", "추가 조사 항목 체크하기"]
        )
    elif category == "notes":
        suggestions.extend(
            ["중요 키워드 정리하기", "요약본 작성하기", "다른 자료와 연결하기"]
        )
    elif category == "ideas":
        suggestions.extend(
            ["아이디어 구체화하기", "실현 가능성 검토하기", "관련 자료 수집하기"]
        )

    # 텍스트 길이에 따른 제안
    if len(text) > 500:
        suggestions.append("긴 내용이므로 요약본 작성 권장")

    return suggestions[:3]  # 최대 3개 제안
