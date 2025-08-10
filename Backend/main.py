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
from api import speech, chat

# 데이터베이스 테이블 생성 - 임시 비활성화
# create_tables()

# FastAPI 앱 생성
app = FastAPI(
    title="역사검증 도우미 API",
    description="조선왕조실록 기반 TTS/STT, OCR, 채팅 및 역사 고증 서비스",
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

# ✅ OCR 라우터 추가 (기존 develop 브랜치 기능 유지)
try:
    from api import ocr
    app.include_router(ocr.router, prefix="/api", tags=["ocr"])
    print("✅ OCR 라우터 등록 완료")
except ImportError as e:
    print(f"⚠️ OCR 라우터 등록 실패: {e}")


@app.get("/")
async def root():
    return {
        "message": "역사검증 도우미 API 서버",
        "version": "1.0.0",
        "services": ["TTS/STT", "Chat", "Historical Chat"],
        "endpoints": {
            "tts": "/api/tts",
            "stt": "/api/stt",
            "chat": "/api/chat",
            "historical_chat": "/api/chat",
            "extract_keywords": "/api/extract-keywords",
            "chat_history": "/api/chat/history/{session_id}",
            "strictness_info": "/api/chat/strictness-info",
            "chat_status": "/api/chat/status",
            "ocr_analyze": "/api/ocr/analyze",
            "ocr_analyze_async": "/api/ocr/analyze-async",
            "ocr_status": "/api/ocr/status/{analysis_id}",
            "docs": "/docs",
            "redoc": "/redoc",
        },
    }


@app.get("/health")
async def health_check():
    """서비스 상태 확인"""
    # TTS/STT 상태
    speech_key = os.getenv("AZURE_SPEECH_KEY")
    speech_region = os.getenv("AZURE_SPEECH_REGION")
    database_url = os.getenv("DATABASE_URL")

    # Historical Chat 환경변수 체크
    azure_oai_key = os.getenv("AZURE_OAI_KEY")
    azure_oai_endpoint = os.getenv("AZURE_OAI_ENDPOINT")
    azure_search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
    azure_search_key = os.getenv("AZURE_SEARCH_KEY")

    # OCR 서비스 상태 확인 (optional)
    try:
        from services.ocr_service import get_available_engines
        ocr_available = True
        ocr_engines = get_available_engines()
    except ImportError:
        logger.info("OCR 서비스를 사용할 수 없습니다 (모듈 없음)")
        ocr_available = False
        ocr_engines = {"paddle": False, "azure": False}

    # Azure OCR 환경변수
    azure_doc_endpoint = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
    azure_doc_key = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_KEY")

    health_status = {
        "status": "healthy",
        "database_configured": bool(database_url),
        "services": {
            # 기본 서비스
            "speech": {
                "configured": bool(speech_key and speech_region),
                "speech_key": "✓" if speech_key else "✗",
                "speech_region": speech_region or "✗",
            },
            "database": {
                "url": database_url or "✗",
                "status": "✓" if database_url else "✗",
            },
            # Historical Chat 서비스
            "historical_chat": {
                "azure_openai_configured": bool(azure_oai_key and azure_oai_endpoint),
                "azure_search_configured": bool(azure_search_endpoint and azure_search_key),
                "rag_available": bool(azure_oai_key and azure_oai_endpoint and azure_search_endpoint and azure_search_key),
                "status": "✓" if azure_oai_key and azure_oai_endpoint else "⚠️"
            },
        }
    }
    
    # OCR 서비스가 사용 가능한 경우에만 추가
    if ocr_available:
        health_status["services"]["ocr"] = {
            "paddle_ocr": {
                "available": ocr_engines.get("paddle", False),
                "status": "✓" if ocr_engines.get("paddle", False) else "✗",
            },
            "azure_ocr": {
                "available": ocr_engines.get("azure", False),
                "status": "✓" if ocr_engines.get("azure", False) else "✗",
            },
        }

    return health_status


@app.on_event("startup")
async def startup_event():
    """서버 시작 시 초기화"""
    logger.info("🚀 역사검증 도우미 API 서버 시작")

    # Historical Chat 서비스 상태 로깅 (수정된 환경변수명 사용)
    azure_oai_configured = bool(os.getenv("AZURE_OPENAI_API_KEY") and os.getenv("AZURE_OPENAI_ENDPOINT"))
    azure_search_configured = bool(os.getenv("AZURE_SEARCH_ENDPOINT") and os.getenv("AZURE_SEARCH_API_KEY"))
    
    logger.info("📊 서비스 상태:")
    logger.info(f"  • Historical Chat (OpenAI): {'✓' if azure_oai_configured else '✗'}")
    logger.info(f"  • Historical Chat (Search): {'✓' if azure_search_configured else '✗'}")
    
    # OCR 서비스 상태 로깅 (가능한 경우)
    try:
        from services.ocr_service import get_available_engines
        ocr_engines = get_available_engines()
        logger.info(f"  • PaddleOCR: {'✓' if ocr_engines.get('paddle', False) else '✗'}")
        logger.info(f"  • Azure OCR: {'✓' if ocr_engines.get('azure', False) else '✗'}")
    except ImportError:
        logger.info(f"  • OCR Services: ⚠️ (모듈 없음)")

    # 환경변수 체크 (수정된 환경변수명 사용)
    missing_vars = []
    if not os.getenv("AZURE_SPEECH_KEY"):
        missing_vars.append("AZURE_SPEECH_KEY")
    if not os.getenv("AZURE_SPEECH_REGION"):
        missing_vars.append("AZURE_SPEECH_REGION")
    if not os.getenv("AZURE_OPENAI_API_KEY"):
        missing_vars.append("AZURE_OPENAI_API_KEY")
    if not os.getenv("AZURE_OPENAI_ENDPOINT"):
        missing_vars.append("AZURE_OPENAI_ENDPOINT")
    if not os.getenv("AZURE_SEARCH_ENDPOINT"):
        missing_vars.append("AZURE_SEARCH_ENDPOINT")
    if not os.getenv("AZURE_SEARCH_API_KEY"):
        missing_vars.append("AZURE_SEARCH_API_KEY")

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

    print("=" * 70)
    print("🚀 역사검증 도우미 API 서버 시작")
    print("=" * 70)
    print(f"📡 서버 주소: http://{host}:{port}")
    print(f"📚 API 문서: http://{host}:{port}/docs")
    print(f"📖 ReDoc: http://{host}:{port}/redoc")
    print(f"💊 Health Check: http://{host}:{port}/health")
    print("=" * 70)
    print("📋 사용 가능한 엔드포인트:")
    print("  • POST /api/tts - 텍스트 음성 변환")
    print("  • POST /api/stt - 음성 텍스트 변환")
    print("  • POST /api/chat - AI 채팅 (고증검증/창작도우미)")
    print("  • POST /api/extract-keywords - 키워드 추출")
    print("  • GET  /api/chat/history/{session_id} - 채팅 기록 조회")
    print("  • GET  /api/chat/status - 역사채팅 상태")
    print("  • GET  /api/chat/strictness-info - 엄격도 설정 정보")
    print("=" * 70)
    print("  💡 채팅 모드:")
    print("    - verification: 조선시대 한국사 고증 채팅 (엄격도 1-5단계)")
    print("    - creative: 창작 도우미 시놉시스 생성 (창작도 1-5단계)")
    print("=" * 70)
    print("  🔧 디버깅 엔드포인트:")
    print("    - GET /api/debug/env - 환경변수 상태 확인")
    print("    - GET /api/debug/azure-search - Azure Search 연결 테스트")
    print("    - GET /api/debug/test-search - 문서 검색 테스트")
    print("=" * 70)

    uvicorn.run(
        app,
        host=host,
        port=port,
        reload=False,  # 프로덕션에서는 False
        log_level="info",
    )
