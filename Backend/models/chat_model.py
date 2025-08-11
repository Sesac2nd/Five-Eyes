from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.sql import func
from config.database import Base


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), index=True)  # 채팅 세션 ID
    message_type = Column(String(10), default="user")  # 'user' 또는 'bot'
    content = Column(Text)  # 메시지 내용
    audio_requested = Column(Boolean, default=False)  # TTS 요청 여부
    is_verify = Column(Boolean, default=False) # 고증 또는 창작 여부 -> True인 경우 고증
    top_n_documents = Column(Integer, default=5) # Azure Search service가 참조할 문서 수 제한
    strictness = Column(Integer, default=2) # 엄격성 설정
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "session_id": self.session_id,
            "message_type": self.message_type,
            "content": self.content,
            "audio_requested": self.audio_requested,
            "is_verify" : self.is_verify,
            "top_n_documents" : self.top_n_documents,
            "strictness" : self.strictness,
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
