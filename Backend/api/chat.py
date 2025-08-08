from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import uuid
import os
import dotenv
import re
import requests
import json
from datetime import datetime
from openai import AzureOpenAI
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from models.chat import ChatMessage, HistoricalChatSession, HistoricalSearchLog
from config.database import get_db

# 환경 변수 로딩
dotenv.load_dotenv()

# Azure 설정
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OAI_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OAI_ENDPOINT")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OAI_API_VER")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OAI_DEPLOY_NAME")
AZURE_OPENAI_MODEL_NAME1 = os.getenv("AZURE_OAI_MODEL_NAME1")  # 창작도우미용 모델
AZURE_OPENAI_EMBEDDING = os.getenv("AZURE_OAI_EMBEDDING")

AZURE_SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
AZURE_SEARCH_INDEX_NAME = os.getenv("AZURE_SEARCH_INDEX_NAME")
AZURE_SEARCH_API_KEY = os.getenv("AZURE_SEARCH_KEY")

# OpenAI 클라이언트
client = None
if AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT:
    client = AzureOpenAI(
        api_key=AZURE_OPENAI_API_KEY,
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        api_version=AZURE_OPENAI_API_VERSION,
    )

# Azure Search 클라이언트
search_client = None
if AZURE_SEARCH_ENDPOINT and AZURE_SEARCH_INDEX_NAME and AZURE_SEARCH_API_KEY:
    search_client = SearchClient(
        endpoint=AZURE_SEARCH_ENDPOINT,
        index_name=AZURE_SEARCH_INDEX_NAME,
        credential=AzureKeyCredential(AZURE_SEARCH_API_KEY)
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



def extract_keywords(query: str) -> List[str]:
    """키워드 추출 함수 - 두 번째 코드 스타일 적용"""
    if not client:
        return []
        
    try:
        prompt = f"""다음 문장에서 한국사 문서 검색을 위한 핵심 키워드 5개만 콤마로 출력:
{query}
키워드:"""
        
        response = client.chat.completions.create(
            model=AZURE_OPENAI_DEPLOYMENT,
            max_tokens=50,
            temperature=0.2,
            messages=[
                {"role": "system", "content": "키워드만 콤마로 출력"},
                {"role": "user", "content": prompt}
            ]
        )
        
        kw_line = response.choices[0].message.content.strip()
        keywords = [kw.strip() for kw in re.split(r'[,\n]', kw_line) if len(kw.strip()) > 0]
        return keywords[:5]  # 최대 5개만
        
    except Exception as e:
        print(f"[키워드 추출 ERROR] {e}")
        return []

def search_documents(keywords: List[str], top_k: int = 5) -> List[dict]:
    """문서 검색 함수 - Azure Search 직접 사용"""
    if not search_client:
        print("❌ Azure Search 클라이언트가 초기화되지 않았습니다.")
        return []
    
    docs = []
    for kw in keywords:
        try:
            print(f"[검색] 키워드: {kw}")
            results = search_client.search(kw, top=top_k, search_mode="any")
            
            for doc in results:
                # 문서 필드명은 실제 인덱스 구조에 맞게 조정 필요
                chunk = doc.get('chunk', '') or doc.get('content', '') or doc.get('text', '')
                ref = doc.get('title', '') or doc.get('source', '') or doc.get('id', '')
                doc_id = doc.get('id', '') or doc.get('document_id', '')
                
                if chunk and len(chunk) > 50:
                    docs.append({
                        "keyword": kw, 
                        "content": chunk, 
                        "ref": ref,
                        "doc_id": doc_id
                    })
                    
        except Exception as e:
            print(f"[검색 오류] 키워드 '{kw}': {e}")
            continue
    
    # 중복 제거 (내용 기준)
    seen = set()
    unique_docs = []
    for d in docs:
        key = d['content'][:60]  # 처음 60자로 중복 판단
        if key not in seen:
            seen.add(key)
            unique_docs.append(d)
    
    print(f"[검색 완료] 총 {len(unique_docs)}개 문서 발견")
    return unique_docs[:3]  # 상위 3개만 반환

def create_verification_response(query: str, docs: List[dict], strictness: int = 3) -> tuple[str, List[str]]:
    """고증 검증 모드 응답 생성: 모든 엄격도에서 fallback 허용"""
    if not client:
        return generate_simple_response(query), ["기본 응답 시스템"]

    try:
        use_fallback = not docs
        context = "\n".join([f"[{d['ref']}] {d['content']}" for d in docs]) if docs else ""

        # ✅ fallback 프롬프트 (사료 없음 시에도 엄격도에 따라 합리적 대응)
        if use_fallback:
            fallback_prompts = {
                1: f"""질문: {query}

사료가 없지만, 한국사 지식과 역사적 맥락을 활용해 자유롭고 유익하게 설명해주세요.

답변:""",
                2: f"""질문: {query}

사료가 없지만, 역사 사실과 배경에 근거하여 정확하고 풍부한 설명을 해주세요.

답변:""",
                3: f"""질문: {query}

사료가 검색되지 않았지만, 알려진 역사적 사실과 공적 문헌에 기반한 설명을 제공해주세요.
출처는 '한국사 일반 지식'으로 간주합니다.

답변:""",
                4: f"""질문: {query}

사료는 없지만, 공신력 있는 한국사 자료에서 확인 가능한 직접적 사실들만 바탕으로 정확하게 설명해주세요.
확실하지 않은 내용은 '**기록 없음**', '**불확실**'로 명시해주세요.

답변:""",
                5: f"""질문: {query}

검색된 사료는 없지만, 정사(正史) 또는 공신력 있는 공식 역사서에 등장하는 사실만 간결하게 설명해주세요.
추측, 해석, 상상 없이 기록된 내용만으로 응답해주세요. 없으면 '기록 없음'이라고 답변해주세요.

답변:"""
            }

            prompt = fallback_prompts.get(strictness, fallback_prompts[3])

            response = client.chat.completions.create(
                model=AZURE_OPENAI_DEPLOYMENT,
                max_tokens=800,
                temperature={1: 0.7, 2: 0.6, 3: 0.5, 4: 0.3, 5: 0.1}[strictness],
                messages=[
                    {"role": "system", "content": "한국사 전문가로서 정확하고 사실 중심의 응답을 해주세요."},
                    {"role": "user", "content": prompt}
                ]
            )

            answer = response.choices[0].message.content.strip()
            return answer, [f"한국사 일반 지식 응답 (사료 없음, 엄격도 {strictness})"]

        # ✅ 사료 존재 시 기존 프롬프트 설계
        if strictness == 1:
            prompt = f"""질문: {query}

아래 검색된 사료와 일반적인 한국사 지식을 바탕으로 자유롭고 유익한 답변을 생성해주세요.

사료:
{context}

답변:"""
        elif strictness == 2:
            prompt = f"""질문: {query}

아래 사료를 중심으로 사실 기반 답변을 하되, 배경 지식도 적절히 활용해주세요.

사료:
{context}

답변:"""
        elif strictness == 3:
            prompt = f"""질문: {query}

아래 검색된 사료만을 중심으로 하고, 출처를 반드시 포함해 사실 위주로 답변해주세요.
만약 해당 정보가 사료에 없다면 '사료에는 해당 정보가 없습니다'라고 먼저 명시한 후, 
일반적인 역사 지식을 기반으로 설명을 이어주세요.

사료:
{context}

답변 (출처 포함):"""
        elif strictness == 4:
            prompt = f"""질문: {query}

사료에 관련된 정보가 있다면 원문을 명확히 인용해주세요.
만약 해당 정보가 사료에 없다면 '사료에는 해당 정보가 없습니다'라고 먼저 명시한 후, 
공신력 있는 역사 지식을 기반으로 설명을 이어주세요.

사료:
{context}

답변 (원문 인용 + 일반 지식 보완):"""
        else:  # strictness == 5
            prompt = f"""질문: {query}

사료 원문 중 질문과 관련된 내용이 있을 경우만 문장을 그대로 인용해주세요.
만약 해당 정보가 사료에 없다면, '사료에 해당 정보가 없습니다.'라고 명시한 후
정사(正史)나 공신력 있는 역사 지식을 기반으로 간결하게 설명해주세요.
추측은 피하고, 기록된 것으로 알려진 사실만 전달해주세요.

사료:
{context}

응답 (사료 인용 → 일반 지식 보완):"""


        response = client.chat.completions.create(
            model=AZURE_OPENAI_DEPLOYMENT,
            max_tokens=1000,
            temperature={1: 0.7, 2: 0.6, 3: 0.5, 4: 0.3, 5: 0.1}[strictness],
            messages=[
                {"role": "system", "content": "정확한 역사적 사실을 바탕으로 한국사 설명을 제공해주세요."},
                {"role": "user", "content": prompt}
            ]
        )

        answer = response.choices[0].message.content.strip()
        sources = [d.get("ref") for d in docs if d.get("ref")] or [f"검색 사료 사용 (엄격도 {strictness})"]
        return answer, sources

    except Exception as e:
        print(f"[검증 응답 생성 오류] {e}")
        return f"❌ 응답 생성 중 오류 발생: {str(e)}", ["오류"]


def create_synopsis(query: str, keywords: List[str], docs: List[dict], strictness: int = 3) -> tuple[str, List[str]]:
    """창작도우미용 시놉시스 생성 - 두 번째 코드 스타일 적용"""
    if not client:
        return "❌ 창작 도우미 모델 설정이 필요합니다.", []
        
    try:
        context = "\n".join([d['content'] for d in docs]) if docs else ""
        creative_prompt = CREATIVE_PROMPTS.get(strictness, CREATIVE_PROMPTS[3])
        
        # 사료가 없을 때도 창작 가능하도록 수정
        if docs:
            synopsis_prompt = f"""질문: {query}
키워드: {', '.join(keywords)}

아래 사료를 참고하여 500자 이내로 드라마틱한 시놉시스를 작성해주세요.

사료:
{context}

창작 지침: {creative_prompt}

시놉시스:"""
        else:
            synopsis_prompt = f"""질문: {query}
키워드: {', '.join(keywords)}

사료는 없지만 한국사 지식을 바탕으로 500자 이내의 드라마틱한 시놉시스를 작성해주세요.

창작 지침: {creative_prompt}

시놉시스:"""
        
        model = AZURE_OPENAI_MODEL_NAME1 if AZURE_OPENAI_MODEL_NAME1 else AZURE_OPENAI_DEPLOYMENT
        
        response = client.chat.completions.create(
            model=model,
            max_tokens=1000,
            temperature={1: 1.0, 2: 0.9, 3: 0.8, 4: 0.6, 5: 0.4}.get(strictness, 0.8),
            messages=[
                {"role": "system", "content": "한국사를 바탕으로 창의적이고 흥미진진한 시놉시스를 작성해주세요."},
                {"role": "user", "content": synopsis_prompt}
            ]
        )
        
        text = response.choices[0].message.content.strip()
        
        # 출처 정보 생성
        sources = []
        if docs:
            for doc in docs:
                if doc.get('ref'):
                    sources.append(f"『{doc['ref']}』")
        
        if not sources:
            sources = ["한국사 지식 기반 창작"]
            
        return text, sources
        
    except Exception as e:
        print(f"[시놉시스 생성 ERROR] {e}")
        return f"❌ 시놉시스를 생성할 수 없습니다: {str(e)}", []

def factual_similarity(synopsis: str, ground_truth: str = "") -> str:
    """사실성 평가 함수"""
    if not client or not ground_truth:
        return "평가 데이터가 없어 사실성 평가를 수행할 수 없습니다."
    
    try:
        prompt = f"""학생이 쓴 요약: {synopsis}
수능특강 설명 원문: {ground_truth}
두 내용의 사실적 일치도(팩트, 시대/주제 부합 등)를 5점 만점으로 수치와 설명으로 평가해줘."""

        response = client.chat.completions.create(
            model=AZURE_OPENAI_DEPLOYMENT,
            max_tokens=500,
            temperature=0.7,
            messages=[
                {"role": "system", "content": "사실성 평가 전문가"},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[사실성 평가 오류] {e}")
        return f"평가 중 오류 발생: {str(e)}"

def generate_simple_response(message: str) -> str:
    """간단한 응답 생성기 (AI 서비스 없을 때 사용)"""
    if "안녕" in message:
        return "안녕하세요! 조선왕조실록 기반 역사 AI입니다. 무엇을 도와드릴까요?"
    elif "세종" in message:
        return "세종대왕(재위 1418-1450)은 조선의 4대 왕으로, 한글 창제와 다양한 문화 정책으로 유명합니다."
    elif "임진왜란" in message:
        return "임진왜란(1592-1598)은 조선 선조 시기에 일본이 조선을 침입한 전쟁입니다."
    else:
        return f"'{message}'에 대한 정보를 조선왕조실록에서 찾아보겠습니다. 좀 더 구체적인 질문을 해주시면 더 정확한 답변을 드릴 수 있습니다."

def debug_azure_search():
    """Azure Search 연결 및 데이터 확인"""
    if not search_client:
        print("❌ Azure Search 클라이언트가 초기화되지 않았습니다.")
        return False
    
    try:
        # 직접 검색 클라이언트로 테스트
        results = search_client.search("세종", top=3)
        doc_count = 0
        for result in results:
            doc_count += 1
            print(f"📄 문서 {doc_count}: {list(result.keys())}")
        
        if doc_count > 0:
            print(f"✅ Azure Search 정상 작동 - {doc_count}개 문서 발견")
            return True
        else:
            print("⚠️ 검색 결과가 없습니다.")
            return False
            
    except Exception as e:
        print(f"❌ Azure Search 연결 오류: {e}")
        return False

# API 엔드포인트들

@router.post("/chat", response_model=ChatResponse)
async def historical_chat(request: ChatRequest, db: Session = Depends(get_db)):
    session_id = request.session_id or str(uuid.uuid4())
    created_at = datetime.utcnow().isoformat()

    strictness = request.strictness or 3
    if strictness not in range(1, 6):
        raise HTTPException(status_code=400, detail="엄격도는 1~5 사이여야 합니다.")

    chat_mode = request.chat_mode or "verification"
    keywords = []
    sources = []

    try:
        # 사용자 메시지 저장
        user_message = ChatMessage(
            session_id=session_id,
            message_type="user",
            content=request.message,
            audio_requested=False
        )
        db.add(user_message)
        db.flush()

        print("\n" + "=" * 50)
        print("❶ [질문에서 뽑아낸 키워드]")
        
        # 1. 키워드 추출
        keywords = extract_keywords(request.message)
        print(keywords)
        
        # 2. 문서 검색
        docs = search_documents(keywords, top_k=5)
        
        if chat_mode == "creative":
            # 창작도우미 모드
            print("\n❷ [답변 시놉시스]")
            synopsis, sources = create_synopsis(request.message, keywords, docs, strictness)
            answer = synopsis
            print(synopsis)
            
        else:
            # 고증 검증 모드
            print("\n❷ [답변 내용]")
            answer, sources = create_verification_response(request.message, docs, strictness)
            print(answer)
        
        print("\n❸ [답변에 활용한 사료 출처]")
        if sources:
            for source in sources:
                print(f"- {source}")
        else:
            print("- 출처 정보 없음")

        # 봇 응답 저장
        bot_message = ChatMessage(
            session_id=session_id,
            message_type="historical_bot" if chat_mode == "verification" else "creative_bot",
            content=answer,
            audio_requested=False
        )
        db.add(bot_message)
        db.commit()

        return ChatResponse(
            id=user_message.id,
            session_id=session_id,
            message=request.message,
            response=answer,
            timestamp=created_at,
            keywords=keywords or ["키워드 없음"],
            sources=sources or ["출처 정보 없음"],
            strictness=strictness,
        )
        
    except Exception as e:
        print(f"[채팅 처리 오류] {e}")
        import traceback
        print(traceback.format_exc())
        db.rollback()
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
        search_ok = bool(search_client is not None)
        creative_ok = bool(AZURE_OPENAI_MODEL_NAME1)

        return ServiceStatus(
            status="healthy" if openai_ok and search_ok else "partial",
            azure_openai_available=openai_ok,
            azure_search_available=search_ok,
            creative_service_available=creative_ok,
            message="모든 설정이 정상입니다." if openai_ok and search_ok and creative_ok else "일부 설정 누락 확인 필요"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"상태 확인 실패: {str(e)}")

@router.get("/chat/strictness-info")
async def get_strictness_info():
    return {
        "verification_strictness": {
            1: {"name": "관대", "description": "추론 가능, 역사 지식 활용", "color": "#10b981"},
            2: {"name": "보통-관대", "description": "사료 + 역사 맥락", "color": "#3b82f6"},
            3: {"name": "보통", "description": "사료 중심, 출처 명시", "color": "#6b7280"},
            4: {"name": "보통-엄격", "description": "사료 원문 위주, 부연 없음", "color": "#f59e0b"},
            5: {"name": "엄격", "description": "사료 원문 외 내용 완전 금지", "color": "#ef4444"},
        },
        "creative_strictness": {
            1: {"name": "자유", "description": "완전 자유 창작, 역사 무시 가능", "color": "#10b981"},
            2: {"name": "보통-자유", "description": "역사적 분위기 + 창의적 해석", "color": "#3b82f6"},
            3: {"name": "보통", "description": "역사적 배경 유지 + 창작적 구성", "color": "#6b7280"},
            4: {"name": "보통-제한", "description": "역사적 사실 기반 + 부분 상상", "color": "#f59e0b"},
            5: {"name": "제한", "description": "철저한 역사적 사실 기반", "color": "#ef4444"},
        }
    }

# 디버깅 엔드포인트들
@router.get("/debug/env")
async def debug_environment():
    """환경변수 설정 상태 확인"""
    env_status = {
        "azure_openai": {
            "api_key": "설정됨" if AZURE_OPENAI_API_KEY else "❌ 없음",
            "endpoint": AZURE_OPENAI_ENDPOINT or "❌ 없음", 
            "api_version": AZURE_OPENAI_API_VERSION or "❌ 없음",
            "deployment": AZURE_OPENAI_DEPLOYMENT or "❌ 없음",
            "model_name1": AZURE_OPENAI_MODEL_NAME1 or "❌ 없음",
            "embedding": AZURE_OPENAI_EMBEDDING or "❌ 없음"
        },
        "azure_search": {
            "endpoint": AZURE_SEARCH_ENDPOINT or "❌ 없음",
            "index_name": AZURE_SEARCH_INDEX_NAME or "❌ 없음", 
            "api_key": "설정됨" if AZURE_SEARCH_API_KEY else "❌ 없음"
        },
        "clients": {
            "openai_initialized": client is not None,
            "search_initialized": search_client is not None
        }
    }
    
    return env_status

@router.get("/debug/azure-search")
async def debug_azure_search_endpoint():
    """Azure Search 상태 디버깅"""
    try:
        is_working = debug_azure_search()
        return {
            "azure_search_working": is_working,
            "endpoint": AZURE_SEARCH_ENDPOINT,
            "index_name": AZURE_SEARCH_INDEX_NAME,
            "api_key_set": bool(AZURE_SEARCH_API_KEY),
            "client_initialized": search_client is not None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"디버깅 실패: {str(e)}")

@router.get("/debug/test-search")
async def test_search_endpoint():
    """문서 검색 테스트"""
    try:
        test_keywords = ["세종대왕", "조선", "한글"]
        
        # 키워드 추출 테스트
        extracted_keywords = extract_keywords("세종대왕의 한글 창제에 대해 알려줘")
        
        # 문서 검색 테스트
        docs = search_documents(test_keywords, top_k=3)
        
        return {
            "test_keywords": test_keywords,
            "extracted_keywords": extracted_keywords,
            "search_results_count": len(docs),
            "search_results": [
                {
                    "keyword": doc.get("keyword", ""),
                    "content_preview": doc.get("content", "")[:100] + "..." if len(doc.get("content", "")) > 100 else doc.get("content", ""),
                    "ref": doc.get("ref", ""),
                    "doc_id": doc.get("doc_id", "")
                }
                for doc in docs
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"검색 테스트 실패: {str(e)}")