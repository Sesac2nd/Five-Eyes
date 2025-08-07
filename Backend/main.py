# main.py
import os
import logging
from dotenv import load_dotenv

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
from api import speech, chat  # OCR import 주석처리

# from api import speech, chat, ocr

# 데이터베이스 테이블 생성
create_tables()

# FastAPI 앱 생성
app = FastAPI(
    title="역사검증 도우미 API",
    description="조선왕조실록 기반 TTS/STT 및 채팅 서비스",  # OCR 제거
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React 개발 서버
        "http://127.0.0.1:3000",
        "http://localhost:5173",  # Vite 개발 서버
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(speech.router, prefix="/api", tags=["speech"])
app.include_router(chat.router, prefix="/api", tags=["chat"])
# OCR 라우터 주석처리
# app.include_router(ocr.router, prefix="/api", tags=["ocr"])


@app.get("/")
async def root():
    return {
        "message": "역사검증 도우미 API 서버",
        "version": "1.0.0",
        "services": ["TTS/STT", "Chat"],  # OCR 제거
        "endpoints": {
            "tts": "/api/tts",
            "stt": "/api/stt",
            "chat": "/api/chat",
            # OCR 엔드포인트 주석처리
            # "ocr": "/api/ocr",
            # "ocr_status": "/api/ocr/status",
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

    # OCR 서비스 상태 확인 - 주석처리
    # from services.paddle_ocr_service import paddle_ocr_service
    # from services.azure_ocr_service import azure_ocr_service

    # Azure OCR 환경변수 - 주석처리
    # azure_doc_endpoint = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
    # azure_doc_key = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_KEY")

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
            # OCR 서비스 주석처리
            # "ocr": {
            #     "paddle_ocr": {
            #         "available": paddle_ocr_service.is_available(),
            #         "status": "✓" if paddle_ocr_service.is_available() else "✗",
            #     },
            #     "azure_ocr": {
            #         "available": azure_ocr_service.is_available(),
            #         "configured": bool(azure_doc_endpoint and azure_doc_key),
            #         "endpoint": azure_doc_endpoint or "✗",
            #         "key": "✓" if azure_doc_key else "✗",
            #         "status": "✓" if azure_ocr_service.is_available() else "✗",
            #     },
            # },
        },
    }


@app.on_event("startup")
async def startup_event():
    """서버 시작 시 초기화"""
    logger.info("🚀 역사검증 도우미 API 서버 시작")

    # OCR 서비스 상태 로깅 - 주석처리
    # from services.paddle_ocr_service import paddle_ocr_service
    # from services.azure_ocr_service import azure_ocr_service

    # logger.info("📊 서비스 상태:")
    # logger.info(f"  • PaddleOCR: {'✓' if paddle_ocr_service.is_available() else '✗'}")
    # logger.info(f"  • Azure OCR: {'✓' if azure_ocr_service.is_available() else '✗'}")

    # 환경변수 체크 - OCR 관련 환경변수 체크 제거
    missing_vars = []
    if not os.getenv("AZURE_SPEECH_KEY"):
        missing_vars.append("AZURE_SPEECH_KEY")
    if not os.getenv("AZURE_SPEECH_REGION"):
        missing_vars.append("AZURE_SPEECH_REGION")
    # OCR 관련 환경변수 체크 주석처리
    # if not os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT"):
    #     missing_vars.append("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
    # if not os.getenv("AZURE_DOCUMENT_INTELLIGENCE_KEY"):
    #     missing_vars.append("AZURE_DOCUMENT_INTELLIGENCE_KEY")

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
    port = int(os.getenv("API_PORT", 8001))

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
    # OCR 엔드포인트 주석처리
    # print("  • POST /api/ocr - 이미지 OCR 분석")
    # print("  • GET  /api/ocr/status - OCR 서비스 상태")
    print("=" * 60)

    uvicorn.run(
        app,
        host=host,
        port=port,
        reload=False,  # 프로덕션에서는 False
        log_level="info",
    )
