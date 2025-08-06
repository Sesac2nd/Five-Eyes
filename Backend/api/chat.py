from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
import uuid
from models.chat import ChatMessage
from config.database import get_db

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    session_id: str = None


class ChatResponse(BaseModel):
    id: int
    session_id: str
    message: str
    response: str
    timestamp: str


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, db: Session = Depends(get_db)):
    """
    채팅 요청 처리
    """
    print(f"=== 채팅 요청 ===")
    print(f"메시지: {request.message}")

    # 세션 ID 생성 또는 사용
    session_id = request.session_id or str(uuid.uuid4())

    try:
        # 사용자 메시지 저장
        user_message = ChatMessage(
            session_id=session_id, message_type="user", content=request.message
        )
        db.add(user_message)
        db.flush()  # ID 가져오기 위해

        # 간단한 응답 생성 (나중에 실제 AI 모델로 교체)
        bot_response = generate_response(request.message)

        # 봇 응답 저장
        bot_message = ChatMessage(
            session_id=session_id, message_type="bot", content=bot_response
        )
        db.add(bot_message)
        db.commit()

        return ChatResponse(
            id=user_message.id,
            session_id=session_id,
            message=request.message,
            response=bot_response,
            timestamp=user_message.created_at.isoformat(),
        )

    except Exception as e:
        print(f"❌ 채팅 오류: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chat/history/{session_id}")
async def get_chat_history(session_id: str, db: Session = Depends(get_db)):
    """
    채팅 기록 조회
    """
    try:
        messages = (
            db.query(ChatMessage)
            .filter(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at)
            .all()
        )

        return [msg.to_dict() for msg in messages]

    except Exception as e:
        print(f"❌ 채팅 기록 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def generate_response(message: str) -> str:
    """
    간단한 응답 생성기 (나중에 실제 AI로 교체)
    """
    if "안녕" in message:
        return "안녕하세요! 조선왕조실록 기반 역사 AI입니다. 무엇을 도와드릴까요?"
    elif "세종" in message:
        return "세종대왕(재위 1418-1450)은 조선의 4대 왕으로, 한글 창제와 다양한 문화 정책으로 유명합니다."
    elif "임진왜란" in message:
        return "임진왜란(1592-1598)은 조선 선조 시기에 일본이 조선을 침입한 전쟁입니다."
    else:
        return f"'{message}'에 대한 정보를 조선왕조실록에서 찾아보겠습니다. 좀 더 구체적인 질문을 해주시면 더 정확한 답변을 드릴 수 있습니다."
