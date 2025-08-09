# Backend/main.py - 수정된 버전
import os
import logging
from dotenv import load_dotenv
import sys

if sys.getdefaultencoding().lower() != "utf-8":
    import importlib

    importlib.reload(sys)
    sys.setdefaultencoding("utf-8")

# 환경변수 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config.database import create_tables
from api import speech, chat, ocr
from config.azure_clients import azure_manager

# 데이터베이스 테이블 생성
create_tables()

# FastAPI 앱 생성
app = FastAPI(
    title="역사검증 도우미 API",
    description="조선왕조실록 기반 TTS/STT, 채팅 및 OCR 서비스",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


@app.on_event("startup")
async def startup_event():
    """앱 시작 시 Azure 클라이언트 상태 확인"""
    try:
        # 클라이언트 연결 테스트
        chat_client = azure_manager.chat_client
        search_client = azure_manager.search_client
        print("✅ Azure 클라이언트 연결 확인 완료")
    except Exception as e:
        print(f"❌ Azure 클라이언트 연결 실패: {e}")


# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://zealous-hill-099c28800.2.azurestaticapps.net/",
        "http://localhost:3000",  # React 개발 서버
        "http://127.0.0.1:3000",
        "http://localhost:5173",  # Vite 개발 서버
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록 (OCR 라우터 포함)
app.include_router(speech.router, prefix="/api", tags=["speech"])
app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(ocr.router, prefix="/api", tags=["ocr"])


@app.get("/")
async def root():
    return {
        "message": "역사검증 도우미 API 서버",
        "version": "1.0.0",
        "services": ["TTS/STT", "Chat", "OCR"],
        "endpoints": {
            "tts": "/api/tts",
            "stt": "/api/stt",
            "chat": "/api/chat",
            "ocr": "/api/ocr/analyze",
            "ocr_async": "/api/ocr/analyze-async",
            "ocr_status": "/api/ocr/status",
            "docs": "/docs",
            "redoc": "/redoc",
        },
    }


@app.get("/health")
async def health_check():
    """서비스 상태 확인"""
    # 기존 TTS/STT 상태
    speech_key = os.getenv("AZURE_SPEECH_KEY")
    speech_region = os.getenv("AZURE_SPEECH_REGION")
    database_url = os.getenv("DATABASE_URL")

    # OCR 서비스 상태 확인
    try:
        from services.ocr_service import get_available_engines

        ocr_engines = get_available_engines()
    except Exception as e:
        ocr_engines = {"paddle": False, "azure": False}
        logger.warning(f"OCR 서비스 상태 확인 실패: {e}")

    return {
        "status": "healthy",
        "database_configured": bool(database_url),
        "services": {
            # 기존 서비스
            "speech": {
                "configured": bool(speech_key and speech_region),
                "speech_key": "✓" if speech_key else "✗",
                "speech_region": speech_region or "✗",
            },
            "database": {
                "url": database_url or "✗",
                "status": "✓" if database_url else "✗",
            },
            # OCR 서비스 상태
            "ocr": {
                "paddle_ocr": {
                    "available": ocr_engines.get("paddle", False),
                    "status": "✓" if ocr_engines.get("paddle", False) else "✗",
                },
                "azure_ocr": {
                    "available": ocr_engines.get("azure", False),
                    "status": "✓" if ocr_engines.get("azure", False) else "✗",
                },
            },
        },
    }


@app.on_event("startup")
async def startup_event_ocr():
    """서버 시작 시 OCR 서비스 초기화"""
    logger.info("🚀 역사검증 도우미 API 서버 시작")

    # OCR 서비스 상태 로깅
    try:
        from services.ocr_service import get_available_engines

        ocr_engines = get_available_engines()
        logger.info("📊 OCR 서비스 상태:")
        logger.info(
            f"  • PaddleOCR: {'✓' if ocr_engines.get('paddle', False) else '✗'}"
        )
        logger.info(f"  • Azure OCR: {'✓' if ocr_engines.get('azure', False) else '✗'}")
    except Exception as e:
        logger.warning(f"OCR 서비스 초기화 중 오류: {e}")

    # 환경변수 체크
    missing_vars = []
    if not os.getenv("AZURE_SPEECH_KEY"):
        missing_vars.append("AZURE_SPEECH_KEY")
    if not os.getenv("AZURE_SPEECH_REGION"):
        missing_vars.append("AZURE_SPEECH_REGION")

    if missing_vars:
        logger.warning(f"⚠️ 누락된 환경변수: {', '.join(missing_vars)}")
        logger.warning("일부 서비스가 제한될 수 있습니다.")


@app.on_event("shutdown")
async def shutdown_event():
    """서버 종료 시 정리"""
    logger.info("🛑 역사검증 도우미 API 서버 종료")


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("PORT", os.getenv("API_PORT", 8000)))

    print("=" * 60)
    print("🚀 역사검증 도우미 API 서버 시작")
    print("=" * 60)
    print(f"📡 서버 주소: http://{host}:{port}")
    print(f"📚 API 문서: http://{host}:{port}/docs")
    print(f"📖 ReDoc: http://{host}:{port}/redoc")
    print(f"💊 Health Check: http://{host}:{port}/health")
    print("=" * 60)
    print("📋 사용 가능한 엔드포인트:")
    print("  • POST /api/tts - 텍스트 음성 변환")
    print("  • POST /api/stt - 음성 텍스트 변환")
    print("  • POST /api/chat - AI 채팅")
    print("  • POST /api/ocr/analyze - 동기식 OCR 분석")
    print("  • POST /api/ocr/analyze-async - 비동기 OCR 분석")
    print("  • GET  /api/ocr/status/{id} - OCR 분석 상태 확인")
    print("  • GET  /api/ocr/result/{id} - OCR 분석 결과 조회")
    print("=" * 60)

    uvicorn.run(
        app,
        host=host,
        port=port,
        reload=False,  # 프로덕션에서는 False
        log_level="info",
    )
