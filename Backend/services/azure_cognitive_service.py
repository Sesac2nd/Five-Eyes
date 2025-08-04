import os
import io
import json
import requests
from typing import Dict, List, Optional
from PIL import Image
import logging
from config.settings import settings

logger = logging.getLogger(__name__)


class AzureCognitiveService:
    """Azure Cognitive Services를 이용한 한자 인식 서비스"""

    def __init__(self):
        self.enabled = False
        self.subscription_key = settings.AZURE_COGNITIVE_KEY
        self.endpoint = settings.AZURE_COGNITIVE_ENDPOINT
        self.ocr_url = None
        self._initialize_service()

    def _initialize_service(self):
        """Azure Cognitive Services 초기화"""
        try:
            if not self.subscription_key or self.subscription_key == "":
                logger.error("❌ Azure Cognitive Services 키가 설정되지 않았습니다.")
                return

            if not self.endpoint or self.endpoint == "":
                logger.error(
                    "❌ Azure Cognitive Services 엔드포인트가 설정되지 않았습니다."
                )
                return

            # OCR API URL 설정
            if not self.endpoint.endswith("/"):
                self.endpoint += "/"

            self.ocr_url = f"{self.endpoint}vision/v3.2/ocr"

            # 연결 테스트
            self._test_connection()

            self.enabled = True
            logger.info("✅ Azure Cognitive Services 초기화 성공")

        except Exception as e:
            logger.error(f"❌ Azure Cognitive Services 초기화 실패: {e}")

    def _test_connection(self):
        """Azure 서비스 연결 테스트"""
        try:
            # 간단한 GET 요청으로 엔드포인트 확인
            headers = {
                "Ocp-Apim-Subscription-Key": self.subscription_key,
            }

            # 테스트용 작은 이미지 생성 (1x1 픽셀)
            test_image = Image.new("RGB", (1, 1), color="white")
            img_byte_arr = io.BytesIO()
            test_image.save(img_byte_arr, format="PNG")
            img_byte_arr = img_byte_arr.getvalue()

            response = requests.post(
                self.ocr_url,
                headers=headers,
                params={"language": "zh-Hans", "detectOrientation": "true"},
                data=img_byte_arr,
                timeout=10,
            )

            if response.status_code in [
                200,
                400,
            ]:  # 400도 연결은 성공 (단지 이미지가 작아서)
                logger.info("✅ Azure Cognitive Services 연결 테스트 성공")
            else:
                raise Exception(f"HTTP {response.status_code}: {response.text}")

        except Exception as e:
            logger.warning(f"⚠️ Azure 연결 테스트 실패: {e}")

    def recognize_text(self, image_bytes: bytes, language: str = "zh-Hans") -> Dict:
        """Azure OCR을 사용한 텍스트 인식"""
        if not self.enabled:
            return {
                "success": False,
                "error": "Azure Cognitive Services가 비활성화되어 있습니다.",
                "text_blocks": [],
            }

        try:
            headers = {
                "Ocp-Apim-Subscription-Key": self.subscription_key,
                "Content-Type": "application/octet-stream",
            }

            params = {"language": language, "detectOrientation": "true"}

            # Azure OCR API 호출
            response = requests.post(
                self.ocr_url,
                headers=headers,
                params=params,
                data=image_bytes,
                timeout=30,
            )

            response.raise_for_status()
            result = response.json()

            # 결과 파싱
            text_blocks = []
            full_text = ""

            if "regions" in result:
                for region in result["regions"]:
                    for line in region["lines"]:
                        line_text = ""
                        line_confidence = []

                        # 단어들을 합쳐서 라인 구성
                        for word in line["words"]:
                            word_text = word["text"]
                            line_text += word_text + " "

                            # Azure OCR은 신뢰도를 제공하지 않으므로 기본값 사용
                            line_confidence.append(0.8)

                        line_text = line_text.strip()
                        if line_text:
                            # 바운딩 박스 정보
                            bbox = line["boundingBox"].split(",")
                            coordinates = {
                                "x": int(bbox[0]),
                                "y": int(bbox[1]),
                                "width": int(bbox[2]),
                                "height": int(bbox[3]),
                            }

                            text_block = {
                                "text": line_text,
                                "confidence": (
                                    sum(line_confidence) / len(line_confidence)
                                    if line_confidence
                                    else 0.8
                                ),
                                "coordinates": coordinates,
                                "language": result.get("language", language),
                            }

                            text_blocks.append(text_block)
                            full_text += line_text + "\n"

            return {
                "success": True,
                "text_blocks": text_blocks,
                "full_text": full_text.strip(),
                "total_blocks": len(text_blocks),
                "orientation": result.get("orientation", "Up"),
                "text_angle": result.get("textAngle", 0),
                "language": result.get("language", language),
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"Azure OCR API 요청 오류: {e}")
            return {
                "success": False,
                "error": f"Azure OCR API 요청 실패: {str(e)}",
                "text_blocks": [],
            }
        except Exception as e:
            logger.error(f"Azure OCR 처리 오류: {e}")
            return {
                "success": False,
                "error": f"텍스트 인식 중 오류가 발생했습니다: {str(e)}",
                "text_blocks": [],
            }

    def recognize_chinese_text(self, image_bytes: bytes) -> Dict:
        """한자 특화 텍스트 인식"""
        # 중국어 간체로 인식 시도
        result_simplified = self.recognize_text(image_bytes, "zh-Hans")

        if result_simplified["success"] and result_simplified["text_blocks"]:
            return {
                **result_simplified,
                "recognition_type": "simplified_chinese",
                "message": "중국어 간체로 인식되었습니다.",
            }

        # 중국어 번체로 재시도
        result_traditional = self.recognize_text(image_bytes, "zh-Hant")

        if result_traditional["success"] and result_traditional["text_blocks"]:
            return {
                **result_traditional,
                "recognition_type": "traditional_chinese",
                "message": "중국어 번체로 인식되었습니다.",
            }

        # 한국어로도 시도 (한자가 포함된 경우)
        result_korean = self.recognize_text(image_bytes, "ko")

        return {
            **result_korean,
            "recognition_type": "korean_with_hanja",
            "message": "한국어 모드로 인식되었습니다.",
        }

    def extract_hanja_characters(self, text_blocks: List[Dict]) -> Dict:
        """한자 문자 추출 및 분석"""
        try:
            hanja_blocks = []

            for block in text_blocks:
                text = block["text"]

                # 한자 문자만 추출
                hanja_chars = ""
                for char in text:
                    # 한자 유니코드 범위
                    if (
                        "\u4e00" <= char <= "\u9fff"  # CJK 통합 한자
                        or "\u3400" <= char <= "\u4dbf"  # CJK 확장 A
                        or "\uf900" <= char <= "\ufaff"
                    ):  # CJK 호환 한자
                        hanja_chars += char

                if hanja_chars:
                    hanja_block = {
                        "original_text": text,
                        "hanja_text": hanja_chars,
                        "confidence": block["confidence"],
                        "coordinates": block["coordinates"],
                        "hanja_count": len(hanja_chars),
                        "language": block.get("language", "unknown"),
                    }
                    hanja_blocks.append(hanja_block)

            return {
                "success": True,
                "hanja_blocks": hanja_blocks,
                "total_hanja_count": sum(b["hanja_count"] for b in hanja_blocks),
                "extraction_summary": f"{len(hanja_blocks)}개 블록에서 {sum(b['hanja_count'] for b in hanja_blocks)}개 한자 추출",
            }

        except Exception as e:
            logger.error(f"한자 추출 오류: {e}")
            return {
                "success": False,
                "error": f"한자 추출 중 오류가 발생했습니다: {str(e)}",
                "hanja_blocks": [],
            }

    def compare_with_ppocr(self, image_bytes: bytes, ppocr_result: Dict) -> Dict:
        """PPOCR 결과와 Azure 결과 비교"""
        try:
            azure_result = self.recognize_chinese_text(image_bytes)

            if not azure_result["success"]:
                return {
                    "success": False,
                    "error": "Azure 인식 실패로 비교할 수 없습니다.",
                    "comparison": {},
                }

            # 텍스트 비교
            ppocr_text = ppocr_result.get("full_text", "")
            azure_text = azure_result.get("full_text", "")

            # 간단한 유사도 계산 (문자 기준)
            similarity = self._calculate_text_similarity(ppocr_text, azure_text)

            comparison = {
                "ppocr_result": {
                    "text": ppocr_text,
                    "blocks_count": len(ppocr_result.get("text_blocks", [])),
                    "avg_confidence": ppocr_result.get("average_confidence", 0),
                },
                "azure_result": {
                    "text": azure_text,
                    "blocks_count": len(azure_result.get("text_blocks", [])),
                    "language": azure_result.get("language", "unknown"),
                },
                "similarity_score": similarity,
                "recommendation": self._get_recommendation(
                    similarity, ppocr_result, azure_result
                ),
            }

            return {
                "success": True,
                "comparison": comparison,
                "combined_confidence": (ppocr_result.get("average_confidence", 0) + 0.8)
                / 2,
            }

        except Exception as e:
            logger.error(f"결과 비교 오류: {e}")
            return {
                "success": False,
                "error": f"결과 비교 중 오류가 발생했습니다: {str(e)}",
                "comparison": {},
            }

    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """두 텍스트 간 유사도 계산 (간단한 문자 기준)"""
        if not text1 and not text2:
            return 1.0
        if not text1 or not text2:
            return 0.0

        # 공백 제거 후 비교
        clean_text1 = "".join(text1.split())
        clean_text2 = "".join(text2.split())

        if clean_text1 == clean_text2:
            return 1.0

        # 간단한 문자별 매칭
        common_chars = set(clean_text1) & set(clean_text2)
        total_chars = set(clean_text1) | set(clean_text2)

        return len(common_chars) / len(total_chars) if total_chars else 0.0

    def _get_recommendation(
        self, similarity: float, ppocr_result: Dict, azure_result: Dict
    ) -> str:
        """비교 결과에 따른 추천사항"""
        if similarity > 0.8:
            return "두 엔진의 결과가 매우 유사합니다. 높은 신뢰도로 인식되었습니다."
        elif similarity > 0.6:
            return "두 엔진의 결과가 유사합니다. 추가 검토를 권장합니다."
        elif similarity > 0.3:
            return "두 엔진의 결과가 다릅니다. 원본 이미지와 결과를 직접 확인해주세요."
        else:
            return "두 엔진의 결과가 크게 다릅니다. 이미지 품질을 확인하거나 다른 방법을 시도해보세요."

    def get_service_info(self) -> Dict:
        """서비스 정보 반환"""
        return {
            "service_name": "Azure Cognitive Services",
            "version": "v3.2",
            "enabled": self.enabled,
            "endpoint": self.endpoint if self.enabled else "Not configured",
            "supported_languages": [
                "zh-Hans (중국어 간체)",
                "zh-Hant (중국어 번체)",
                "ko (한국어)",
                "ja (일본어)",
                "en (영어)",
            ],
            "features": [
                "다국어 OCR",
                "텍스트 방향 감지",
                "바운딩 박스 정보",
                "언어 자동 감지",
                "한자 특화 인식",
            ],
        }


# 전역 서비스 인스턴스
azure_cognitive_service = AzureCognitiveService()
