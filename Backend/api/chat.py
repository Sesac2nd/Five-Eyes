import os
import uuid
from dotenv import load_dotenv
from config.database import get_db

from models.chat_model import ChatMessage
from services.chat_service import generate_response
from fastapi import APIRouter, HTTPException, Depends

from pydantic import BaseModel
from typing import List, Union
from sqlalchemy.orm import Session

load_dotenv()
IS_DEBUG = os.getenv("IS_DEBUG" "")

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    session_id: Union[str, None] = None
    is_verify: bool = False
    top_n_documents: int = 5
    strictness: int = 2

class ChatResponse(BaseModel):
    id: int
    session_id: str
    message: str
    response: str
    timestamp: str
    keywords: List[str]
    sources: List[str]
    # source_mapping: List[str]
    # additional_info: List[str]

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, db: Session = Depends(get_db)):
    """
    채팅 요청 처리
    """
    print(f"=== 채팅 요청 ===")
    print(f"메시지: {request.message}\n\
고증여부 :{'고증' if request.is_verify else '창작'}\n\
문서개수:{request.top_n_documents}\n엄격성:{request.strictness}")

    # 세션 ID 생성 또는 사용
    session_id = request.session_id or str(uuid.uuid4())

    try:
        # 사용자 메시지 저장
        user_message = ChatMessage(
            session_id=session_id,
            content=request.message,
            is_verify=request.is_verify,
            top_n_documents=request.top_n_documents,
            strictness=request.strictness
        )
        db.add(user_message)
        db.flush()  # ID 가져오기 위해

        # 응답 생성
        bot_response = generate_response(request.message)
        if IS_DEBUG:
            print(f"bot_Resp txt : {bot_response.message}")
            print(f"bot_Resp kwd : {bot_response.keywords}")
            print(f"bot_Resp src : {bot_response.sources}")
        # 봇 응답 저장
        bot_message = ChatMessage(
            session_id=session_id,
            message_type="bot",
            content=bot_response.message
        )
        db.add(bot_message)
        db.commit()

        return ChatResponse(
            id=user_message.id,
            session_id=session_id,
            message=request.message,
            response=bot_response.message,
            keywords=bot_response.keywords,
            sources=bot_response.sources,
            # source_mapping=bot_response.source_mapping,
            # additional_info=bot_response.additional_info,
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