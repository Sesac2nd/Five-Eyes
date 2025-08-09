#!/usr/bin/env python3
# main.py - 최소화 버전 (테스트용)
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 환경변수 기본값
PORT = int(os.getenv("PORT", "8000"))
HOST = os.getenv("HOST", "0.0.0.0")

# FastAPI 앱 생성
app = FastAPI(
    title="역사검증 도우미 API - 테스트",
    description="Azure App Service 배포 테스트",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://zealous-hill-099c28800.2.azurestaticapps.net",
        "http://localhost:3000",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 기본 엔드포인트
@app.get("/")
async def root():
    return {
        "message": "역사검증 도우미 API 서버 실행 중",
        "status": "healthy",
        "port": PORT,
        "host": HOST
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "역사검증 도우미 API",
        "version": "1.0.0"
    }

# 서버 시작 (로컬 테스트용)
if __name__ == "__main__":
    import uvicorn
    print(f"🚀 서버 시작: http://{HOST}:{PORT}")
    uvicorn.run(app, host=HOST, port=PORT)
