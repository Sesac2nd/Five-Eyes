from typing import Dict, List, Union
from config.azure_clients import get_chat_client, get_search_client, get_chat_model, get_keyword_model
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

chat_key = os.getenv("AZURE_OPENAI_API_KEY", "")
chat_model = os.getenv("AZURE_OAI_MODEL_NAME", "")
chat_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "")
chat_api_version = os.getenv("AZURE_OAI_API_VER", "")
chat_deploy = os.getenv("AZURE_OAI_DEPLOY_NAME", "")

keyword_model = os.getenv("AZURE_OAI_KEYWORD_MODEL_NAME", "")

search_key = os.getenv("AZURE_SEARCH_API_KEY", "")
search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT", "")
search_index = os.getenv("AZURE_SEARCH_INDEX_NAME", "")

class ChatResponse:
    """채팅 응답 데이터 클래스 - 기존 서비스 호환용"""
    def __init__(self,
                 message: str, keywords: Union[List[str], None] = None,
                 sources: Union[List[str], None] = None,
                 source_mapping: Union[List[str], None] = None,
                 additional_info: Union[List[str], None] = None):
        self.message = message
        self.keywords = keywords or []
        self.sources = sources or []
        self.source_maping = source_mapping or []
        self.additional_info = additional_info or []

def generate_response(message: str, is_verify: bool = False) -> ChatResponse:
    """
    기존 서비스용 호환 함수 - 새로운 API로 위임
    """
    try:
        # ⚠️ 새로운 API 함수들을 사용하거나, 간단한 폴백 응답 제공
        # 실제로는 새로운 chat API의 함수들을 사용할 수 있습니다
        
        # 간단한 폴백 응답 (임시)
        if "안녕" in message:
            response_text = "안녕하세요! 조선왕조실록 기반 역사 AI입니다."
        elif "세종" in message:
            response_text = "세종대왕(재위 1418-1450)은 조선의 4대 왕으로, 한글 창제와 다양한 문화 정책으로 유명합니다."
        else:
            response_text = f"'{message}'에 대한 답변입니다. 새로운 API 시스템으로 전환되었습니다."
        
        return ChatResponse(
            message=response_text,
            keywords=["조선왕조실록", "역사"],
            sources=["한국사 DB"]
        )
        
    except Exception as e:
        print(f"❌ 호환 응답 생성 오류: {e}")
        return ChatResponse(
            message=f"죄송합니다. '{message}'에 대한 응답을 생성하는 중 오류가 발생했습니다.",
            keywords=[],
            sources=[]
        )

# 나머지 기존 함수들은 유지하되, 실제 구현은 새로운 시스템에 위임
def extract_keyword_from_query(query_text: str, OAI_client: AzureOpenAI, keyword_model: str) -> List[str]:
    """RAG용 키워드 추출 - 기존 호환용"""
    try:
        # 새로운 extract_keywords 함수로 위임하거나 간단한 키워드 반환
        simple_keywords = query_text.split()[:3]  # 임시 구현
        return simple_keywords
    except Exception as e:
        print(f"키워드 추출 오류: {e}")
        return [query_text]
