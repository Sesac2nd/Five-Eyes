import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()

# Azure PostgreSQL 환경변수
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER") 
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME")  # database_chat
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_SSL_MODE = os.getenv("DB_SSL_MODE", "require")

# Azure PostgreSQL 연결 URL 구성 (모든 설정을 URL에 포함)
DATABASE_URL = (
    os.getenv("DATABASE_URL") or
    f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?sslmode={DB_SSL_MODE}&connect_timeout=30&application_name=FiveEyes_HistoricalChat"
)

# SQLAlchemy 엔진 설정 (connect_args 완전 제거)
engine = create_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """데이터베이스 세션 의존성"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_connection():
    """데이터베이스 연결 테스트"""
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"✅ Azure PostgreSQL 연결 성공!")
            print(f"   • PostgreSQL 버전: {version.split(',')[0]}")
            print(f"   • 호스트: {DB_HOST}")
            print(f"   • 데이터베이스: {DB_NAME}")
            print(f"   • SSL 모드: {DB_SSL_MODE}")
            return True
    except Exception as e:
        print(f"❌ 데이터베이스 연결 실패: {e}")
        print(f"   • 연결 URL: postgresql://{DB_USER}:***@{DB_HOST}:{DB_PORT}/{DB_NAME}")
        print(f"   • SSL 모드: {DB_SSL_MODE}")
        return False

def create_tables():
    """테이블 생성 및 상태 확인"""
    try:
        # 연결 테스트 먼저 수행
        if not test_connection():
            print("❌ 데이터베이스 연결 실패로 테이블 생성을 건너뜁니다.")
            return False
            
        # 모델 import
        from models.chat import ChatMessage, SpeechLog, HistoricalChatSession, HistoricalSearchLog
        
        # OCR 모델은 존재할 때만 import
        ocr_available = True
        try:
            from models.ocr_model import OCRAnalysis
        except ImportError:
            print("⚠️ OCR 모델을 찾을 수 없습니다. OCR 테이블은 생성되지 않습니다.")
            ocr_available = False
        
        # 테이블 생성
        Base.metadata.create_all(bind=engine)
        
        # 생성된 테이블 확인
        with engine.connect() as connection:
            result = connection.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name
            """))
            tables = [row[0] for row in result.fetchall()]
            
        print("✅ Azure PostgreSQL: 데이터베이스 테이블 생성 완료")
        print(f"   • 생성된 테이블: {', '.join(tables)}")
        
        # 예상 테이블 확인
        expected_tables = ['chat_messages', 'historical_chat_sessions', 'historical_search_logs', 'speech_logs']
        if ocr_available:
            expected_tables.append('ocr_analyses')
            
        missing_tables = [table for table in expected_tables if table not in tables]
        if missing_tables:
            print(f"   ⚠️ 누락된 테이블: {', '.join(missing_tables)}")
        else:
            print("   ✅ 모든 예상 테이블이 생성되었습니다.")
            
        return True
        
    except Exception as e:
        print(f"❌ 테이블 생성 실패: {e}")
        return False

def get_table_info():
    """테이블 정보 조회 (디버깅용)"""
    try:
        with engine.connect() as connection:
            # 테이블별 레코드 수 확인
            tables_info = {}
            
            # 테이블 존재 확인 후 카운트
            table_names = ['chat_messages', 'historical_chat_sessions', 'historical_search_logs', 'speech_logs']
            
            for table_name in table_names:
                try:
                    result = connection.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                    tables_info[table_name] = result.fetchone()[0]
                except Exception as e:
                    tables_info[table_name] = f"오류: {e}"
            
            return tables_info
            
    except Exception as e:
        print(f"❌ 테이블 정보 조회 실패: {e}")
        return {}

# 간단한 연결 테스트용 함수
def simple_connection_test():
    """간단한 연결 테스트 (외부에서 호출용)"""
    try:
        # 가장 기본적인 연결 테스트 (최소 설정)
        simple_url = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?sslmode={DB_SSL_MODE}"
        test_engine = create_engine(simple_url, pool_pre_ping=True)
        
        with test_engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            result.fetchone()
            print("✅ 기본 연결 테스트 성공")
            return True
            
    except Exception as e:
        print(f"❌ 기본 연결 테스트 실패: {e}")
        return False

if __name__ == "__main__":
    # 직접 실행 시 연결 테스트
    print("=== Azure PostgreSQL 연결 테스트 ===")
    
    # 기본 연결 테스트
    if simple_connection_test():
        # 테이블 생성 테스트
        create_tables()
        
        # 테이블 정보 조회
        print("\n=== 테이블 정보 ===")
        info = get_table_info()
        for table, count in info.items():
            print(f"   • {table}: {count}")
    else:
        print("기본 연결에 실패했습니다. 환경변수를 확인하세요.")
