import os
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # 기본 서버 설정
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    ENVIRONMENT: str = "development"

    # CORS 설정
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]

    # 데이터베이스 설정
    DATABASE_URL: str = "sqlite:///./histpath.db"

    # JWT 토큰 설정
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7일

    # Azure 서비스 설정
    AZURE_SPEECH_KEY: str = ""
    AZURE_SPEECH_REGION: str = "koreacentral"
    AZURE_COGNITIVE_KEY: str = ""
    AZURE_COGNITIVE_ENDPOINT: str = ""
    AZURE_OPENAI_KEY: str = ""  # 추후 구현
    AZURE_OPENAI_ENDPOINT: str = ""  # 추후 구현
    AZURE_OPENAI_VERSION: str = "2024-02-01"  # 추후 구현

    # PPOCR 설정
    PPOCR_USE_GPU: bool = False
    PPOCR_USE_ANGLE_CLS: bool = True
    PPOCR_LANG: str = "ch"  # 중국어(한문) 인식
    PPOCR_DET_MODEL_DIR: str = ""  # 모델 경로 (선택사항)
    PPOCR_REC_MODEL_DIR: str = ""  # 모델 경로 (선택사항)

    # 파일 처리 설정
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_IMAGE_EXTENSIONS: List[str] = [".jpg", ".jpeg", ".png", ".bmp", ".tiff"]
    ALLOWED_AUDIO_EXTENSIONS: List[str] = [".wav", ".mp3", ".m4a", ".ogg"]

    # 조선왕조실록 데이터 설정
    SILLOK_XML_PATH: str = "./data/sillok_xml/"
    SILLOK_PROCESS_BATCH_SIZE: int = 100

    # 로그 설정
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "histpath.log"

    class Config:
        env_file = ".env"
        case_sensitive = True


# 전역 설정 인스턴스
settings = Settings()


# 환경별 설정 검증
def validate_settings():
    """필수 환경변수 검증"""
    required_vars = []

    if not settings.AZURE_SPEECH_KEY:
        required_vars.append("AZURE_SPEECH_KEY")

    if not settings.AZURE_COGNITIVE_KEY:
        required_vars.append("AZURE_COGNITIVE_KEY")

    if required_vars:
        print(f"⚠️ 다음 환경변수가 설정되지 않았습니다: {', '.join(required_vars)}")
        print("📝 .env 파일을 확인하고 필요한 Azure 서비스 키를 설정해주세요.")

    return len(required_vars) == 0


# 개발 환경 설정
def get_dev_config():
    """개발 환경 전용 설정"""
    return {"reload": True, "debug": True, "log_level": "debug"}


# 운영 환경 설정
def get_prod_config():
    """운영 환경 전용 설정"""
    return {"reload": False, "debug": False, "log_level": "info"}
