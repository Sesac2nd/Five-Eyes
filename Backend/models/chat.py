from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON
from sqlalchemy.sql import func
from config.database import Base


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), index=True)  # 채팅 세션 ID
    message_type = Column(String(20))  # 'user', 'bot', 'historical_bot'
    content = Column(Text)  # 메시지 내용
    audio_requested = Column(Boolean, default=False)  # TTS 요청 여부

    # ✅ 아래 항목들은 들여쓰기를 맞춰 class 안에 넣어야 함
    keywords = Column(JSON, nullable=True)          # 추출된 키워드 리스트
    ai_evaluation = Column(Text, nullable=True)     # AI 평가 결과
    strictness_level = Column(Integer, nullable=True)  # 고증 엄격도
    response_metadata = Column(JSON, nullable=True)  # 기타 메타데이터

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "session_id": self.session_id,
            "message_type": self.message_type,
            "content": self.content,
            "audio_requested": self.audio_requested,
            "keywords": self.keywords,
            "ai_evaluation": self.ai_evaluation,
            "strictness_level": self.strictness_level,
            "response_metadata": self.response_metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }



class SpeechLog(Base):
    __tablename__ = "speech_logs"

    id = Column(Integer, primary_key=True, index=True)
    service_type = Column(String(10))  # 'tts' 또는 'stt'
    input_text = Column(Text)  # TTS 입력 텍스트 또는 STT 결과
    success = Column(Boolean)  # 성공 여부
    error_message = Column(Text, nullable=True)  # 에러 메시지
    audio_length = Column(Integer, nullable=True)  # 오디오 길이 (bytes)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "service_type": self.service_type,
            "input_text": self.input_text,
            "success": self.success,
            "error_message": self.error_message,
            "audio_length": self.audio_length,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# Historical Chat 전용 모델 추가
class HistoricalChatSession(Base):
    __tablename__ = "historical_chat_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), unique=True, index=True)
    user_name = Column(String(100), nullable=True)  # 사용자 이름 (선택)
    session_title = Column(String(200), nullable=True)  # 세션 제목
    total_messages = Column(Integer, default=0)  # 총 메시지 수
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_activity = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "session_id": self.session_id,
            "user_name": self.user_name,
            "session_title": self.session_title,
            "total_messages": self.total_messages,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_activity": self.last_activity.isoformat() if self.last_activity else None,
        }


class HistoricalSearchLog(Base):
    """Historical Search 로그 (검색 통계용)"""
    __tablename__ = "historical_search_logs"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), index=True)
    query = Column(Text)  # 검색 쿼리
    keywords = Column(JSON)  # 추출된 키워드
    strictness_level = Column(Integer)  # 검색 엄격도
    response_length = Column(Integer, nullable=True)  # 응답 길이
    processing_time = Column(Integer, nullable=True)  # 처리 시간 (ms)
    success = Column(Boolean, default=True)  # 성공 여부
    error_message = Column(Text, nullable=True)  # 에러 메시지
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "session_id": self.session_id,
            "query": self.query,
            "keywords": self.keywords,
            "strictness_level": self.strictness_level,
            "response_length": self.response_length,
            "processing_time": self.processing_time,
            "success": self.success,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }