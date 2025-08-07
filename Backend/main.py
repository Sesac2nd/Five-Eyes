import os
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config.database import create_tables
from api import speech, chat
from config.azure_clients import azure_manager

# 데이터베이스 테이블 생성
create_tables()

# FastAPI 앱 생성
app = FastAPI(
    title="역사검증 도우미 API",
    description="조선왕조실록 기반 TTS/STT 및 채팅 서비스",
    version="1.0.0",
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
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(speech.router, prefix="/api", tags=["speech"])
app.include_router(chat.router, prefix="/api", tags=["chat"])


@app.get("/")
async def root():
    return {
        "message": "역사검증 도우미 API 서버",
        "version": "1.0.0",
        "endpoints": {
            "tts": "/api/tts",
            "stt": "/api/stt",
            "chat": "/api/chat",
            "docs": "/docs",
        },
    }


@app.get("/health")
async def health_check():
    """서비스 상태 확인"""
    speech_key = os.getenv("AZURE_SPEECH_KEY")
    speech_region = os.getenv("AZURE_SPEECH_REGION")
    database_url = os.getenv("DATABASE_URL")

    return {
        "status": "healthy",
        "azure_speech_configured": bool(speech_key and speech_region),
        "database_configured": bool(database_url),
        "services": {
            "speech_key": "✓" if speech_key else "✗",
            "speech_region": speech_region or "✗",
            "database": database_url or "✗",
        },
    }


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", 8001))

    print(f"🚀 서버 시작: http://{host}:{port}")
    print(f"📚 API 문서: http://{host}:{port}/docs")

    uvicorn.run(app, host=host, port=port)
