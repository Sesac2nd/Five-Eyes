# services/azure_ocr_service.py
import os
import time
import logging
import numpy as np
from typing import List, Dict, Optional
from dotenv import load_dotenv
from utils.image_processing import ImageProcessor
from utils.text_processing import HistoricalDocumentTextProcessor
from models.ocr import WordResult, LineResult

load_dotenv()
logger = logging.getLogger(__name__)


class AzureOCRService:
    """Azure Document Intelligence OCR 서비스 - 범용"""

    def __init__(self):
        self.client = None
        self.enabled = False
        self._initialize_azure_client()

    def _initialize_azure_client(self):
        """Azure Document Intelligence 클라이언트 초기화"""
        try:
            # Azure SDK 임포트 (지연 로딩)
            from azure.core.credentials import AzureKeyCredential
            from azure.ai.documentintelligence import DocumentIntelligenceClient
            from azure.ai.documentintelligence.models import AnalyzeDocumentRequest

            # 환경변수에서 설정 읽기
            endpoint = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
            key = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_KEY")

            if not endpoint or not key:
                logger.error(
                    "❌ Azure Document Intelligence 환경변수가 설정되지 않았습니다."
                )
                logger.info("필요한 환경변수:")
                logger.info("- AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
                logger.info("- AZURE_DOCUMENT_INTELLIGENCE_KEY")
                self.enabled = False
                return

            # 클라이언트 생성
            self.client = DocumentIntelligenceClient(
                endpoint=endpoint, credential=AzureKeyCredential(key)
            )

            # 연결 테스트 (간단한 요청으로)
            logger.info("🔗 Azure Document Intelligence 연결 테스트 중...")
            # 실제 연결 테스트는 첫 요청 시 확인

            self.enabled = True
            logger.info("✅ Azure Document Intelligence 초기화 성공")
            logger.info(f"Endpoint: {endpoint}")

        except ImportError as e:
            logger.error(f"Azure SDK가 설치되지 않음: {e}")
            logger.info("설치 명령어: pip install azure-ai-documentintelligence")
            self.enabled = False
        except Exception as e:
            logger.error(f"Azure Document Intelligence 초기화 실패: {e}")
            self.enabled = False

    def is_available(self) -> bool:
        """서비스 사용 가능 여부"""
        return self.enabled and self.client is not None

    def process_image(self, image_data: bytes) -> Dict:
        """이미지 OCR 처리 메인 함수"""
        if not self.is_available():
            return {
                "success": False,
                "error": "Azure Document Intelligence 서비스가 비활성화되어 있습니다.",
                "processing_time": 0.0,
            }

        start_time = time.time()

        try:
            # Azure SDK 임포트 (함수 내부에서)
            from azure.ai.documentintelligence.models import AnalyzeDocumentRequest

            # 1. 이미지 전처리
            logger.info("🔄 Azure용 이미지 전처리 시작")
            processed_image = ImageProcessor.enhance_image_for_ocr(image_data, "azure")

            # 2. Azure Document Intelligence API 호출
            logger.info("📡 Azure Document Intelligence API 호출 중...")

            analyze_request = AnalyzeDocumentRequest(bytes_source=processed_image)

            # 비동기 분석 시작
            poller = self.client.begin_analyze_document(
                model_id="prebuilt-read",  # 일반 텍스트 읽기 모델
                analyze_request=analyze_request,
            )

            # 결과 대기
            logger.info("⏳ Azure 분석 완료 대기 중...")
            result = poller.result()

            # 3. 결과 처리
            processed_result = self._process_azure_result(result)

            processing_time = time.time() - start_time
            logger.info(f"✅ Azure OCR 처리 완료 ({processing_time:.2f}초)")

            return {
                "success": True,
                "processing_time": processing_time,
                **processed_result,
            }

        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"❌ Azure OCR 처리 실패: {e}")

            # 에러 타입별 상세 메시지
            error_message = str(e)
            if "401" in error_message or "Unauthorized" in error_message:
                error_message = "Azure API 키가 유효하지 않습니다."
            elif "403" in error_message or "Forbidden" in error_message:
                error_message = (
                    "Azure API 접근이 거부되었습니다. 구독 상태를 확인하세요."
                )
            elif "429" in error_message or "rate limit" in error_message.lower():
                error_message = "Azure API 요청 한도를 초과했습니다."
            elif "timeout" in error_message.lower():
                error_message = "Azure API 요청 시간이 초과되었습니다."

            return {
                "success": False,
                "error": f"Azure OCR 처리 중 오류: {error_message}",
                "processing_time": processing_time,
            }

    def _process_azure_result(self, azure_result) -> Dict:
        """Azure 결과를 통일된 형태로 변환"""
        if (
            not azure_result
            or not hasattr(azure_result, "pages")
            or not azure_result.pages
        ):
            return {
                "lines": [],
                "full_text": "",
                "word_count": 0,
                "confidence_avg": 0.0,
            }

        try:
            # Azure 결과에서 단어 정보 추출
            words_data = []

            for page in azure_result.pages:
                if hasattr(page, "words") and page.words:
                    for word in page.words:
                        # Azure 결과 구조
                        text = word.content if hasattr(word, "content") else ""
                        confidence = (
                            word.confidence if hasattr(word, "confidence") else 1.0
                        )

                        # polygon 정보 추출
                        polygon = []
                        if hasattr(word, "polygon") and word.polygon:
                            polygon = list(word.polygon)

                        # bbox 계산
                        if polygon and len(polygon) >= 8:
                            x_coords = [polygon[i] for i in range(0, len(polygon), 2)]
                            y_coords = [polygon[i] for i in range(1, len(polygon), 2)]

                            min_x = min(x_coords)
                            max_x = max(x_coords)
                            min_y = min(y_coords)
                            max_y = max(y_coords)

                            bbox = [
                                int(min_x),
                                int(min_y),
                                int(max_x - min_x),
                                int(max_y - min_y),
                            ]
                            center_x = (min_x + max_x) / 2
                            center_y = (min_y + max_y) / 2
                        else:
                            # polygon이 없는 경우 기본값
                            bbox = [0, 0, 100, 20]
                            center_x = 50
                            center_y = 10

                        words_data.append(
                            {
                                "text": text,
                                "confidence": float(confidence),
                                "polygon": polygon,
                                "bbox": bbox,
                                "center_x": center_x,
                                "center_y": center_y,
                            }
                        )

            if not words_data:
                return {
                    "lines": [],
                    "full_text": "",
                    "word_count": 0,
                    "confidence_avg": 0.0,
                }

            # 역사문서 텍스트 처리기로 정렬
            processor = HistoricalDocumentTextProcessor()
            vertical_lines = processor.group_words_by_lines(words_data)

            # LineResult 객체들 생성
            lines = []
            all_confidences = []
            full_text_parts = []

            for line_idx, line_words in enumerate(vertical_lines):
                # 라인별 통계 계산
                line_confidences = [w["confidence"] for w in line_words]
                line_texts = [w["text"] for w in line_words]

                # 라인 바운딩 박스 계산
                if line_words:
                    all_bboxes = [w["bbox"] for w in line_words]
                    min_x = min(bbox[0] for bbox in all_bboxes)
                    min_y = min(bbox[1] for bbox in all_bboxes)
                    max_x = max(bbox[0] + bbox[2] for bbox in all_bboxes)
                    max_y = max(bbox[1] + bbox[3] for bbox in all_bboxes)
                    line_bbox = [min_x, min_y, max_x - min_x, max_y - min_y]
                else:
                    line_bbox = [0, 0, 0, 0]

                # WordResult 객체들 생성
                word_results = []
                for word in line_words:
                    word_result = WordResult(
                        text=word["text"],
                        confidence=word["confidence"],
                        bbox=word["bbox"],
                        polygon=word["polygon"] if word["polygon"] else None,
                    )
                    word_results.append(word_result)

                # LineResult 생성
                line_result = LineResult(
                    line_number=line_idx + 1,
                    words=word_results,
                    full_text="".join(line_texts),
                    avg_confidence=(
                        np.mean(line_confidences) if line_confidences else 0.0
                    ),
                    bbox=line_bbox,
                )

                lines.append(line_result)
                all_confidences.extend(line_confidences)
                full_text_parts.extend(line_texts)

            return {
                "lines": lines,
                "full_text": "".join(full_text_parts),
                "word_count": len(words_data),
                "confidence_avg": np.mean(all_confidences) if all_confidences else 0.0,
            }

        except Exception as e:
            logger.error(f"Azure OCR 결과 처리 실패: {e}")
            return {
                "lines": [],
                "full_text": "",
                "word_count": 0,
                "confidence_avg": 0.0,
            }


# 전역 인스턴스
azure_ocr_service = AzureOCRService()
