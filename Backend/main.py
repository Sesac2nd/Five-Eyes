from fastapi import FastAPI, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
import os
from dotenv import load_dotenv
import base64
from datetime import datetime
import logging
import traceback

# 환경 변수 로드
load_dotenv()

# 로깅 설정
if not logging.getLogger().handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
logger = logging.getLogger(__name__)

# FastAPI 앱 초기화
app = FastAPI(
    title="TTS API Only",
    version="1.0.0",
    description="Azure Speech 기반 TTS 전용 API 서버",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------- Pydantic Models -------------------


class TTSRequest(BaseModel):
    text: str
    voice_name: Optional[str] = "ko-KR-HyunsuMultilingualNeural"


class TTSResponse(BaseModel):
    success: bool
    audio_data: Optional[str] = None
    error: Optional[str] = None
    voice_name: str
    text: str


# ------------------- Azure TTS Function -------------------


async def azure_text_to_speech(text: str, voice_name: str) -> TTSResponse:
    try:
        import azure.cognitiveservices.speech as speechsdk

        speech_key = os.getenv("AZURE_SPEECH_KEY")
        speech_region = os.getenv("AZURE_SPEECH_REGION", "koreacentral")

        if not speech_key:
            logger.error("Azure Speech Key가 없음")
            return TTSResponse(
                success=False,
                error="Azure Speech Key가 설정되지 않았습니다.",
                voice_name=voice_name,
                text=text,
            )

        speech_config = speechsdk.SpeechConfig(
            subscription=speech_key, region=speech_region
        )
        speech_config.speech_synthesis_voice_name = voice_name

        # 메모리 스트림 방식 시도 (권장)
        pull_stream = speechsdk.audio.PullAudioOutputStream()
        audio_config = speechsdk.audio.AudioOutputConfig(stream=pull_stream)
        synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=speech_config, audio_config=audio_config
        )

        logger.info(f"[TTS] 요청: '{text}' (voice: {voice_name})")
        result = synthesizer.speak_text_async(text.strip()).get()

        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            audio_data = result.audio_data
            if audio_data and len(audio_data) > 0:
                audio_base64 = base64.b64encode(audio_data).decode("utf-8")
                return TTSResponse(
                    success=True,
                    audio_data=audio_base64,
                    voice_name=voice_name,
                    text=text,
                )
            else:
                raise Exception("오디오 데이터가 비어있음")

        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = result.cancellation_details
            error_msg = f"TTS 취소: {cancellation_details.reason} - {cancellation_details.error_details or ''}"
            logger.error(error_msg)
            raise Exception(error_msg)

        else:
            logger.error(f"TTS 실패: {result.reason}")
            raise Exception(f"TTS 실패: {result.reason}")

    except ImportError:
        return TTSResponse(
            success=False,
            error="Azure Speech SDK가 설치되지 않았습니다.",
            voice_name=voice_name,
            text=text,
        )
    except Exception as e:
        logger.error(f"TTS 처리 오류: {e}")
        logger.error(f"오류 상세: {traceback.format_exc()}")
        return TTSResponse(
            success=False, error=str(e), voice_name=voice_name, text=text
        )


# ------------------- API Endpoints -------------------


@app.post("/api/tts", response_model=TTSResponse)
async def text_to_speech_form(
    text: str = Form(...), voice_name: str = Form("ko-KR-HyunsuMultilingualNeural")
):
    """텍스트를 Azure TTS로 변환(Form 방식)"""
    if not text or len(text.strip()) == 0:
        raise HTTPException(status_code=400, detail="텍스트가 비어있습니다.")
    if len(text) > 1000:
        raise HTTPException(
            status_code=400, detail="텍스트가 너무 깁니다(1000자 제한)."
        )
    return await azure_text_to_speech(text, voice_name)


@app.post("/api/tts-json", response_model=TTSResponse)
async def text_to_speech_json(request: TTSRequest):
    """텍스트를 Azure TTS로 변환(JSON 방식)"""
    if not request.text or len(request.text.strip()) == 0:
        raise HTTPException(status_code=400, detail="텍스트가 비어있습니다.")
    if len(request.text) > 1000:
        raise HTTPException(
            status_code=400, detail="텍스트가 너무 깁니다(1000자 제한)."
        )
    return await azure_text_to_speech(
        request.text, request.voice_name or "ko-KR-HyunsuMultilingualNeural"
    )


@app.get("/api/voices")
async def get_available_voices():
    """Azure 한국어 음성 목록 및 기본값 제공"""
    return {
        "korean_voices": [
            {
                "name": "ko-KR-HyunsuMultilingualNeural",
                "gender": "Male",
                "description": "한국어 남성(다국어 가능)",
            },
            {
                "name": "ko-KR-SunHiNeural",
                "gender": "Female",
                "description": "한국어 여성",
            },
            {
                "name": "ko-KR-InJoonNeural",
                "gender": "Male",
                "description": "한국어 남성",
            },
            {
                "name": "ko-KR-BongJinNeural",
                "gender": "Male",
                "description": "한국어 남성",
            },
            {
                "name": "ko-KR-GookMinNeural",
                "gender": "Male",
                "description": "한국어 남성",
            },
        ],
        "default": "ko-KR-HyunsuMultilingualNeural",
    }


@app.post("/api/navigation-tts", response_model=TTSResponse)
async def navigation_tts(request: TTSRequest):
    """네비게이션 안내음 중심 TTS(API 단순화)"""
    # 200자 초과는 자동 줄이기
    text = request.text[:200] + "..." if len(request.text) > 200 else request.text
    common_phrases = {
        "목적지 확인": "목적지를 확인했습니다. 경로를 탐색하겠습니다.",
        "경로 탐색": "경로를 탐색 중입니다. 잠시만 기다려주세요.",
        "안내 시작": "안내를 시작합니다.",
        "직진": "직진하세요.",
        "우회전": "우회전하세요.",
        "좌회전": "좌회전하세요.",
        "도착": "목적지에 도착했습니다.",
    }
    for key, phrase in common_phrases.items():
        if key in text or phrase in text:
            text = phrase
            break
    return await azure_text_to_speech(
        text, request.voice_name or "ko-KR-HyunsuMultilingualNeural"
    )


@app.get("/test/voice")
async def test_voice_service():
    """TTS 서비스 동작 테스트"""
    test_text = "안녕하세요. Azure 음성 서비스 테스트입니다."
    test_request = TTSRequest(
        text=test_text, voice_name="ko-KR-HyunsuMultilingualNeural"
    )
    result = await azure_text_to_speech(test_text, test_request.voice_name)
    audio_size = len(base64.b64decode(result.audio_data)) if result.audio_data else 0
    return {
        "success": result.success,
        "message": "서비스 정상" if result.success else "음성 서비스 테스트 실패",
        "audio_size": audio_size,
        "test_text": test_text,
        "error": result.error if not result.success else None,
    }


# 심플 상태 확인
@app.get("/")
async def root():
    return {
        "message": "Azure Speech TTS 전용 API",
        "version": "1.0.0",
        "time": datetime.now().isoformat(),
        "endpoints": [
            "/api/tts",
            "/api/tts-json",
            "/api/voices",
            "/api/navigation-tts",
            "/test/voice",
        ],
    }


if __name__ == "__main__":
    import uvicorn

    logger.info("🚀 Azure Speech TTS API 서버 시작 (포트: 8000)")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
