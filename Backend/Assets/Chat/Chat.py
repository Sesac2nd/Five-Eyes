import os
import json
from dotenv import load_dotenv
from openai import AzureOpenAI
from typing import Dict, List, Union

from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential

import traceback

load_dotenv()
DEBUG_FLAG = os.getenv("IS_DEBUG", "")

chat_key = os.getenv("AZURE_OAI_KEY", "")
chat_model = os.getenv("AZURE_OAI_MODEL_NAME", "")
chat_endpoint = os.getenv("AZURE_OAI_ENDPOINT", "")
chat_api_version = os.getenv("AZURE_OAI_API_VER", "")
chat_deploy = os.getenv("AZURE_OAI_DEPLOY_NAME", "")

keyword_model = os.getenv("AZURE_OAI_KEYWORD_MODEL_NAME", "")

search_key = os.getenv("AZURE_SEARCH_KEY", "")
search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT", "")
search_index = os.getenv("AZURE_SEARCH_INDEX_NAME", "")

chat_client = AzureOpenAI(
    api_version=chat_api_version,
    azure_endpoint=chat_endpoint,
    api_key=chat_key,
)

search_client = SearchClient(
    endpoint=search_endpoint,
    index_name=search_index,
    credential=AzureKeyCredential(search_key)
)

def extract_keyword_from_query(query_text:str, OAI_client:AzureOpenAI, keyword_model : str) -> List[str]:
    """
    RAG용 키워드 추출
    """
    keyword_prompt = f"""Query: {query_text}
    
    위 Query에서 주요 키워드를 추출하세요.
    인물명, 지명, 제도명, 사건명 등 사용자의 질문에 적절한 답변을 할 수 있는 문서를 찾아 질문에 사용할 수 있도록 핵심적인 키워드를 중심으로 최대 5개까지 추출하세요.

    추출 조건:
    1. 핵심적인 키워드만 추출
    2. 고유명사를 우선적으로 선택
    3. 검색 가능한 구체적인 용어 선택
    4. 중복을 피하고 중요도 순으로 정렬
    5. 제공된 Query에 존재하지 않는 내용은 금지됨

    키워드 목록 (JSON 배열 형태로만 응답):"""
    try:
        keyword_response = OAI_client.chat.completions.create(
            model=keyword_model,
            messages=[
                {"role": "system", "content": "당신은 한국사 키워드 추출 전문가입니다. 정확한 JSON 배열 형태로만 응답하세요."},
                {"role": "user", "content": keyword_prompt}
            ],
            temperature=0.3,
            max_tokens=200
        )
        
        keywords_text = keyword_response.choices[0].message.content.strip()
        if keywords_text[0] == "[" and keywords_text[-1] == "]":
            keywords = json.loads(keywords_text)
            return keywords if isinstance(keywords, list) else []
        else:
            print(f"쿼리 키워드 추출 오류 -> 추출값 : {keywords_text}")
            raise Exception
    
    except Exception as e:
        print(f"쿼리 키워드 추출 중 오류 발생: {traceback.format_exc() if DEBUG_FLAG else e}")
        return []
    
def extract_keywords_from_response(response_text: str, OAI_client:AzureOpenAI, keyword_model:str) -> List[str]:
    """Chat model 응답에서 키워드 추출"""
    keyword_prompt = f"""다음 텍스트에서 주요 키워드를 추출하세요.
    인물명, 지명, 제도명, 사건명 등 사용자가 답변의 내용이 적절히 생성되었는지 판단할 수 있는 키워드를 중심으로 최대 5개까지 추출하세요.

    텍스트: {response_text}

    추출 조건:
    1. 핵심적인 키워드만 추출
    2. 고유명사를 우선적으로 선택
    3. 검색 가능한 구체적인 용어 선택
    4. 중복을 피하고 중요도 순으로 정렬
    5. 제공된 텍스트에 존재하지 않는 내용은 금지됨

    키워드 목록 (JSON 배열 형태로만 응답):"""

    try:
        keyword_response = OAI_client.chat.completions.create(
            model=keyword_model,
            messages=[
                {"role": "system", "content": "당신은 한국사 키워드 추출 전문가입니다. 정확한 JSON 배열 형태로만 응답하세요."},
                {"role": "user", "content": keyword_prompt}
            ],
            temperature=0.3,
            max_tokens=200
        )
        
        keywords_text = keyword_response.choices[0].message.content.strip()
        if keywords_text[0] == "[" and keywords_text[-1] == "]":
            keywords = json.loads(keywords_text)
            return keywords if isinstance(keywords, list) else []
        else:
            print(f"응답 키워드 추출 오류 -> 추출값 : {keywords_text}")
            raise Exception
    
    except Exception as e:
        print(f"응답 키워드 추출 중 오류 발생: {traceback.format_exc() if DEBUG_FLAG else e}")
        return []

def format_sources(documents: List[Dict]) -> List[str]:
    """문서 목록을 출처 형태로 포맷팅"""
    sources = []
    for doc in documents:
        # source(파일명)을 주 출처로 사용
        if doc.get("source"):
            source_info = doc["source"]
            
            # chunk_id가 있으면 추가 정보로 포함
            if doc.get("chunk_id"):
                # chunk_id에서 페이지 정보 추출 시도
                chunk_id = doc["chunk_id"]
                if "pages_" in chunk_id:
                    page_num = chunk_id.split("pages_")[-1]
                    source_info += f" (페이지 {page_num})"
                else:
                    source_info += f" (ID: {chunk_id})"
            
            sources.append(source_info)
        
        # source가 없으면 chunk_id라도 사용
        elif doc.get("chunk_id"):
            sources.append(f"문서 ID: {doc['chunk_id']}")
    
    return list(set(sources))  # 중복 제거

def get_suggestion(return_type: str, search_client:SearchClient) -> List[str]:
    """
    DB 기반 제안 기능
    로직 변경 & 구현 필요
    """
    if return_type == "query":
        try:
            # DB에서 인기 검색어나 추천 쿼리를 가져오는 로직
            # 현재는 Azure Search에서 자주 검색되는 용어들을 기반으로 생성
            popular_searches = search_client.search(
                search_text="*",
                top=50,
                select=["title", "content"],
                include_total_count=True
            )
            
            # 검색 결과에서 자주 등장하는 주제들을 추출하여 쿼리 형태로 변환
            query_suggestions = []
            common_topics = ["세종대왕", "조선시대", "임진왜란", "영조", "정조"]
            
            for topic in common_topics:
                topic_results = search_client.search(
                    search_text=topic,
                    top=1
                )
                for result in topic_results:
                    if result.get("title"):
                        query_suggestions.append(f"{topic}에 대해 더 자세히 알려주세요")
                        break
            
            result = query_suggestions[:5] if query_suggestions else [
                "조선시대에 대해 궁금한 것이 있으면 언제든 물어보세요!"
            ]
            
        except Exception as e:
            print(f"쿼리 제안 생성 오류: {traceback.format_exc() if DEBUG_FLAG else e}")
            result = ["조선시대 역사에 대해 궁금한 점을 물어보세요."]
        
        return result
        
    elif return_type == "keyword":
        try:
            # DB에서 인기 키워드를 추출
            search_results = search_client.search(
                search_text="*",
                top=100,
                select=["content", "title"]
            )
            
            # 키워드 빈도 분석을 위한 간단한 로직
            keyword_counts = {}
            common_keywords = ["세종대왕", "한글창제", "조선시대", "과거제도", 
                             "임진왜란", "이순신", "영조", "탕평책", "정조", "규장각"]
            
            for keyword in common_keywords:
                try:
                    count_results = search_client.search(
                        search_text=keyword,
                        include_total_count=True
                    )
                    keyword_counts[keyword] = count_results.get("@odata.count", 0)
                except:
                    keyword_counts[keyword] = 0
            
            # 빈도순으로 정렬하여 상위 키워드 반환
            sorted_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)
            result = [keyword for keyword, count in sorted_keywords[:10]]
            
        except Exception as e:
            print(f"키워드 제안 생성 오류: {traceback.format_exc() if DEBUG_FLAG else e}")
            result = ["세종대왕", "조선시대", "임진왜란"]
        
        return result
    else:
        raise ValueError("Allowed return type is ['query', 'keyword'].")

def get_text_completion_result(
        Query: Dict[str, str], 
        OAI_client: AzureOpenAI,
        search_client: SearchClient,
        chat_model: str,
        keyword_model: str,
        is_verify: bool = False 
    ) -> Dict[str, Union[List, str]]:
    """
    챗봇 응답 생성 메인 함수 (Azure Search 통합 버전)
    
    Args:
        Query: {"query": "사용자 질문", "context": "이전 대화 컨텍스트(선택)"}
        OAI_Client: Azure OpenAI 클라이언트
        search_client : Azure Search Service 클라이언트
        chat_model : 답변 생성에 사용할 Azure OpenAI 모델 이름
        keyword_model : keyword 추출에 사용할 Azure OpenAI 모델 이름
        is_verify: True면 고증 모드, False면 창작 모드

    Returns:
        {
            "query_suggestions": [...],  # 컨텍스트 없을 때만
            "response": "AI 응답",
            "doc_search_keywords": ["키워드1", ...], # 문서 추출용 키워드
            "resp_keywords": ["키워드1", ...], # 답변 내용 파악용 키워드
            "sources": ["출처1", ...]
        }
    """
    
    user_query = Query.get("query", "")
    context = Query.get("context", "")
    
    result = {
        "response": "",
        "doc_search_keywords": [],
        "resp_keywords": [],
        "sources": []
    }
    
    # 컨텍스트가 없으면 쿼리 제안 추가
    if not context and not user_query:
        result["query_suggestions"] = get_suggestion("query", search_client)
        result["response"] = "안녕하세요! 저는 역사적 사료 기반의 역사 AI입니다. 역사에 대한 궁금한 점을 물어보세요."
        return result
    
    if not user_query:
        result["response"] = "질문을 입력해주세요."
        return result
    
    try:
        # 1. 모드에 따른 시스템 프롬프트 설정
        if is_verify:
            system_prompt = """당신은 역사 전문가입니다. 다음 규칙을 엄격히 준수하세요:
                1. 제공된 문서에 명시된 내용만을 기반으로 답변하세요
                2. 문서에 없는 정보는 절대 추측하거나 생성하지 마세요
                3. 확실하지 않은 내용은 "제공된 자료에서는 해당 정보를 찾을 수 없습니다"라고 명시하세요
                4. 모든 답변에 구체적인 출처를 포함하세요
                5. 문서 범위를 벗어나는 질문에는 "관련 자료가 부족합니다"라고 답변하세요
            """
            strictness = 4  # 높은 엄격성
        else:
            system_prompt = "당신은 역사 전문가입니다. 제공된 자료를 기반으로 하되, 창작을 위한 상상력을 발휘하여 답변하세요."
            strictness = 2  # 낮은 엄격성
        
        # 2. data_sources 설정
        data_sources = [{
            "type": "azure_search",
            "parameters": {
                "endpoint": search_endpoint,
                "index_name": search_index,
                "query_type": "semantic",
                "in_scope": True,
                "strictness": strictness,  # 핵심: 엄격성 설정
                "top_n_documents": 5,
                "authentication": {
                        "key": search_key,
                        "type": "api_key"
                    }
            }
        }]
        
        # 3. 모드에 따른 파라미터 설정
        temperature = 0.3 if is_verify else 0.7
        max_tokens = 1000 if is_verify else 1200
        
        # 4. Azure OpenAI API 호출 (data_sources 포함)
        response = OAI_client.chat.completions.create(
            model=chat_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_query}
            ],
            extra_body={"data_sources" : data_sources},  # 핵심: data_sources 추가
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        OAI_response = response.choices[0].message.content
        if OAI_response == None:
            result["response"] = "죄송합니다. 일시적인 오류가 발생했습니다. 다시 시도해주세요."
            return result
        
        # 5. 키워드 추출 (응답에서만)
        keywords = extract_keywords_from_response(OAI_response, OAI_client, keyword_model)
        
        # 6. 출처 정보 추출 (Azure OpenAI가 자동 제공)
        sources = []

        if hasattr(response.choices[0].message, 'context'):
            # Azure OpenAI가 제공하는 출처 정보 추출
            context_data = response.choices[0].message.context
            if context_data and 'citations' in context_data:
                sources = [citation.get('title', 'Unknown') for citation in context_data['citations']]
        
        result.update({
            "response": OAI_response,
            "resp_keywords": keywords,
            "sources": sources
        })
        print("="*100)
        print(OAI_response)
        print("="*100)
    except Exception as e:
        print(f"응답 생성 오류: {traceback.format_exc() if DEBUG_FLAG else e}")
        result["response"] = "죄송합니다. 일시적인 오류가 발생했습니다. 다시 시도해주세요."
    
    return result

def get_relevant_documents(query: str, search_client:SearchClient, top_k: int = 5) -> List[Dict]:
    """Azure Search를 통한 관련 문서 검색"""
    try:
        search_results = search_client.search(
            search_text=query,
            top=top_k,
            include_total_count=True
        )
        
        documents = []
        for result in search_results:
            documents.append({
                "content": result.get("chunk", ""),  # chunk를 content로 매핑
                "source": result.get("title", ""),  # title(파일명)을 source로 매핑
                "title": [],  # 빈 배열로 설정, 추후 column 설정 필요.
                "king": [],  # 빈 배열로 설정
                "date": [],  # 빈 배열로 설정
                "chunk_id": result.get("chunk_id", ""), # chunk_id for page_mapping
                "score": result.get("@search.score", 0),
                "reranker_score": result.get("@search.rerankerScore", 0),
                "highlights": result.get("@search.highlights", {}),
                "captions": result.get("@search.captions", [])
            })
        
        return documents
    except Exception as e:
        print(f"문서 검색 오류: {traceback.format_exc() if DEBUG_FLAG else e}")
        return []
    

# example
qt = "통일 신라의 독서삼품과에 대해 설명하고, 그것이 통일신라에 어떠한 기여를 했는지 알려줘."
query = {"query" : f"{qt}"}
resp = get_text_completion_result(query, chat_client, search_client, chat_model, keyword_model, True)
print(resp)