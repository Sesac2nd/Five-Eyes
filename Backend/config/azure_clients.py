import os
from dotenv import load_dotenv
from openai import AzureOpenAI
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential

load_dotenv()

class AzureClientManager:
    """Azure 클라이언트들을 싱글톤으로 관리"""
    _instance = None
    _chat_client = None
    _search_client = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AzureClientManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._initialize_clients()
            self._initialized = True
    
    def _initialize_clients(self):
        """클라이언트 초기화"""
        try:
            # OpenAI 클라이언트 설정
            chat_key = os.getenv("AZURE_OAI_KEY", "")
            chat_endpoint = os.getenv("AZURE_OAI_ENDPOINT", "")
            chat_api_version = os.getenv("AZURE_OAI_API_VER", "")
            
            self._chat_client = AzureOpenAI(
                api_version=chat_api_version,
                azure_endpoint=chat_endpoint,
                api_key=chat_key,
            )
            
            # Search 클라이언트 설정
            search_key = os.getenv("AZURE_SEARCH_KEY", "")
            search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT", "")
            search_index = os.getenv("AZURE_SEARCH_INDEX_NAME", "")
            
            self._search_client = SearchClient(
                endpoint=search_endpoint,
                index_name=search_index,
                credential=AzureKeyCredential(search_key)
            )
            
            print("✅ Azure 클라이언트 초기화 완료")
            
        except Exception as e:
            print(f"❌ Azure 클라이언트 초기화 실패: {e}")
            raise
    
    @property
    def chat_client(self):
        """OpenAI 클라이언트 반환"""
        if self._chat_client is None:
            raise Exception("Chat client가 초기화되지 않았습니다.")
        return self._chat_client
    
    @property
    def search_client(self):
        """Search 클라이언트 반환"""
        if self._search_client is None:
            raise Exception("Search client가 초기화되지 않았습니다.")
        return self._search_client
    
    @property
    def chat_model(self):
        return os.getenv("AZURE_OAI_MODEL_NAME", "")
    
    @property
    def keyword_model(self):
        return os.getenv("AZURE_OAI_KEYWORD_MODEL_NAME", "")

# 전역 인스턴스 생성 (모듈 임포트 시 한 번만 실행)
azure_manager = AzureClientManager()

# 편의 함수들
def get_chat_client():
    return azure_manager.chat_client

def get_search_client():
    return azure_manager.search_client

def get_chat_model():
    return azure_manager.chat_model

def get_keyword_model():
    return azure_manager.keyword_model