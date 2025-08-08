from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import uuid
import os
import dotenv
import re
from datetime import datetime
from openai import AzureOpenAI

# 환경 변수 로딩
dotenv.load_dotenv()

# Azure 설정
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OAI_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OAI_ENDPOINT")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OAI_API_VER")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OAI_DEPLOY_NAME")
AZURE_OPENAI_MODEL_NAME1 = os.getenv("AZURE_OAI_MODEL_NAME1")  # 창작도우미용 모델

AZURE_SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
AZURE_SEARCH_INDEX_NAME = os.getenv("AZURE_SEARCH_INDEX_NAME")
AZURE_SEARCH_API_KEY = os.getenv("AZURE_SEARCH_KEY")

# OpenAI 클라이언트 (같은 엔드포인트 사용)
client = AzureOpenAI(
    api_key=AZURE_OPENAI_API_KEY,
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    api_version=AZURE_OPENAI_API_VERSION,
)

SYSTEM_PROMPTS = {
    1: "벡터 검색된 사료와 일반적인 역사 지식을 바탕으로 자유롭게 답변해줘.",
    2: "벡터 검색된 사료를 중심으로, 필요시 맥락을 보태 이야기를 구성해줘.",
    3: "검색된 사료만 이용하며 출처를 명시해줘.",
    4: "검색된 사료에 기록된 내용만 표현하고 원문 인용이 반드시 있어야 해.",
    5: "사료 원문만 인용하고 해석은 금지야. 사료에 없다면 '없음'으로 답해.",
}

# 창작 엄격도 프롬프트
CREATIVE_PROMPTS = {
    1: "완전히 자유로운 창작으로, 역사적 사실과 다르더라도 흥미로운 스토리를 만들어줘.",
    2: "역사적 분위기는 유지하되, 창의적인 해석과 상상력을 더해서 시놉시스를 작성해줘.",
    3: "역사적 배경은 정확히 유지하면서, 인물과 사건은 창작적으로 구성해줘.",
    4: "역사적 사실을 기반으로 하되, 기록에 없는 부분만 상상력으로 채워서 작성해줘.",
    5: "철저히 역사적 사실에 기반해서, 확인된 기록 위주로 시놉시스를 작성해줘.",
}

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    strictness: Optional[int] = 3
    chat_mode: Optional[str] = "verification"  # verification 또는 creative

class ChatResponse(BaseModel):
    id: int
    session_id: str
    message: str
    response: str
    timestamp: str
    keywords: List[str]
    sources: List[str]
    strictness: int

class KeywordRequest(BaseModel):
    message: str

class KeywordResponse(BaseModel):
    keywords: List[str]

class ServiceStatus(BaseModel):
    status: str
    azure_openai_available: bool
    azure_search_available: bool
    creative_service_available: bool
    message: str

def doc_id_to_title(doc_id: str) -> str:
    mapping = {
        "doc11": "황현, 『오하기문』(25013-0044)",
        "doc12": "과거 제도 관련 자료(25013-0041)",
        "doc18": "탕평 정치 관련 자료(25013-0043)",
        "doc26": "조선 후기 정치 변동 자료(25013-0042)",
        "doc27": "조선 후기 사회상 관련 기록(25013-0045)",
    }
    return mapping.get(doc_id, f"[출처 ID: {doc_id}]")

def create_rag_data_sources(strictness=3, top_k=30):
    strictness_to_top_k = {
        1: 50,
        2: 40,
        3: 30,
        4: 20,
        5: 10
    }
    return [{
        "type": "azure_search",
        "parameters": {
            "endpoint": AZURE_SEARCH_ENDPOINT,
            "index_name": AZURE_SEARCH_INDEX_NAME,
            "authentication": {"type": "api_key", "key": AZURE_SEARCH_API_KEY},
            "strictness": strictness,
            "top_n_documents": strictness_to_top_k.get(strictness, top_k),
            "in_scope": True
        }
    }]

def generate_response_rag(message: str, strictness: int = 3) -> (str, List[str]):
    try:
        prompt = SYSTEM_PROMPTS.get(strictness, SYSTEM_PROMPTS[3])
        response = client.chat.completions.create(
            model=AZURE_OPENAI_DEPLOYMENT,
            max_tokens=1024,
            temperature={1: 0.9, 2: 0.8, 3: 0.7, 4: 0.5, 5: 0.3}.get(strictness, 0.7),
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"{message} (엄격도: {strictness})"},
            ],
            extra_body={"data_sources": create_rag_data_sources(strictness)},
        )

        content = response.choices[0].message.content.strip()
        content = re.sub(r"\[doc\d+\]", "", content).strip()

        sources = []
        if hasattr(response.choices[0], "context"):
            for ctx in response.choices[0].context.get("messages", []):
                name = ctx.get("name")
                if name and name not in sources:
                    sources.append(name)

        mapped_sources = [doc_id_to_title(s) for s in sources if s]
        return content, mapped_sources

    except Exception as e:
        print(f"[RAG ERROR] {e}")
        return f"❌ AI 응답을 생성할 수 없습니다: {str(e)}", []

def extract_keywords_creative(message: str) -> List[str]:
    """창작도우미용 키워드 추출"""
    try:
        prompt = f"다음 문장에서 핵심 키워드 3~5개를 ,로 구분해서 추출해줘: {message}"
        
        response = client.chat.completions.create(
            model=AZURE_OPENAI_MODEL_NAME1,
            max_tokens=100,
            temperature=0.7,
            messages=[
                {"role": "system", "content": "너는 한국사 키워드 추출 전문가야. 헛된 말 없이 키워드만 출력해."},
                {"role": "user", "content": prompt},
            ],
        )
        return [kw.strip() for kw in response.choices[0].message.content.strip().split(",")]
    except Exception as e:
        print(f"[창작 키워드 ERROR] {e}")
        return []

def create_synopsis(query: str, keywords: List[str], strictness: int = 3) -> str:
    """창작도우미용 시놉시스 생성"""
    try:
        creative_prompt = CREATIVE_PROMPTS.get(strictness, CREATIVE_PROMPTS[3])
        
        synopsis_prompt = (
            f"다음 키워드를 참고해서, '{query}'에 대해 400~500자 분량의 시놉시스를 작성해줘:\n"
            f"키워드: {', '.join(keywords)}\n\n"
            f"창작 지침: {creative_prompt}"
        )
        
        response = client.chat.completions.create(
            model=AZURE_OPENAI_MODEL_NAME1,
            max_tokens=700,
            temperature={1: 1.0, 2: 0.9, 3: 0.8, 4: 0.6, 5: 0.4}.get(strictness, 0.8),
            messages=[
                {"role": "system", "content": "너는 전문 작가이자 역사 스토리텔러야."},
                {"role": "user", "content": synopsis_prompt},
            ],
        )
        
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[시놉시스 생성 ERROR] {e}")
        return f"❌ 시놉시스를 생성할 수 없습니다: {str(e)}"

def extract_keywords(message: str) -> List[str]:
    try:
        prompt = f"다음 문장에서 핵심 키워드 3~5개를 ,로 구분해서 추출해줘: {message}"

        response = client.chat.completions.create(
            model=AZURE_OPENAI_DEPLOYMENT,
            max_tokens=100,
            temperature=0.7,
            messages=[
                {"role": "system", "content": "너는 한국사 키워드 추출 전문가야. 헛된 말 없이 키워드만 출력해."},
                {"role": "user", "content": prompt},
            ],
        )
        return [kw.strip() for kw in response.choices[0].message.content.strip().split(",")]
    except Exception as e:
        print(f"[키워드 ERROR] {e}")
        return []

@router.post("/chat", response_model=ChatResponse)
async def historical_chat(request: ChatRequest):
    session_id = request.session_id or str(uuid.uuid4())
    created_at = datetime.utcnow().isoformat()

    strictness = request.strictness or 3
    if strictness not in range(1, 6):
        raise HTTPException(status_code=400, detail="엄격도는 1~5 사이여야 합니다.")

    chat_mode = request.chat_mode or "verification"

    try:
        if chat_mode == "creative":
            # 창작도우미 모드
            keywords = extract_keywords_creative(request.message)
            synopsis = create_synopsis(request.message, keywords, strictness)
            
            # 시놉시스 형식으로 응답 구성
            answer = f"✨ **창작 도우미 시놉시스**\n\n{synopsis}"
            sources = ["창작 도우미 AI"]
            
        else:
            # 고증 검증 모드 (기존)
            keywords = extract_keywords(request.message)
            answer, sources = generate_response_rag(request.message, strictness)

        return ChatResponse(
            id=0,
            session_id=session_id,
            message=request.message,
            response=answer,
            timestamp=created_at,
            keywords=keywords,
            sources=sources or ["출처 정보 없음"],
            strictness=strictness,
        )
    except Exception as e:
        print(f"[채팅 처리 오류] {e}")
        raise HTTPException(status_code=500, detail=f"채팅 오류: {str(e)}")

@router.post("/extract-keywords", response_model=KeywordResponse)
async def extract_keywords_endpoint(request: KeywordRequest):
    try:
        keywords = extract_keywords(request.message)
        return KeywordResponse(keywords=keywords)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"키워드 추출 오류: {str(e)}")

@router.get("/chat/status", response_model=ServiceStatus)
async def get_service_status():
    try:
        openai_ok = bool(AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_DEPLOYMENT)
        search_ok = bool(AZURE_SEARCH_ENDPOINT and AZURE_SEARCH_INDEX_NAME and AZURE_SEARCH_API_KEY)
        creative_ok = bool(AZURE_OPENAI_MODEL_NAME1)

        return ServiceStatus(
            status="healthy" if openai_ok and search_ok and creative_ok else "partial",
            azure_openai_available=openai_ok,
            azure_search_available=search_ok,
            creative_service_available=creative_ok,
            message="모든 설정이 정상입니다." if openai_ok and search_ok and creative_ok else "일부 설정 누락 확인 필요"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"상태 확인 실패: {str(e)}")

# @router.get("/chat/strictness-info")
# async def get_strictness_info():
#     return {
#         "verification_strictness": {
#             1: {"name": "관대", "description": "추론 가능, 역사 지식 활용", "color": "#10b981"},
#             2: {"name": "보통-관대", "description": "사료 + 역사 맥락", "color": "#3b82f6"},
#             3: {"name": "보통", "description": "사료 중심, 출처 명시", "color": "#6b7280"},
#             4: {"name": "보통-엄격", "description": "사료 원문 위주, 부연 없음", "color": "#f59e0b"},
#             5: {"name": "엄격", "description": "사료 원문 외 내용 완전 금지", "color": "#ef4444"},
#         },
#         "creative_strictness": {
#             1: {"name": "자유", "description": "완전 자유 창작, 역사 무시 가능", "color": "#10b981"},
#             2: {"name": "보통-자유", "description": "역사적 분위기 + 창의적 해석", "color": "#3b82f6"},
#             3: {"name": "보통", "description": "역사적 배경 유지 + 창작적 구성", "color": "#6b7280"},
#             4: {"name": "보통-제한", "description": "역사적 사실 기반 + 부분 상상", "color": "#f59e0b"},
#             5: {"name": "제한", "description": "철저한 역사적 사실 기반", "color": "#ef4444"},
#         }
#    }