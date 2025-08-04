import os
import cv2
import numpy as np
from typing import List, Dict, Optional, Tuple
from PIL import Image
import logging
from config.settings import settings

logger = logging.getLogger(__name__)


class PPOCRService:
    """PPOCR를 이용한 한문 인식 서비스"""

    def __init__(self):
        self.enabled = False
        self.ocr = None
        self._initialize_ppocr()

    def _initialize_ppocr(self):
        """PPOCR 초기화"""
        try:
            from paddleocr import PaddleOCR

            # PPOCR 설정
            self.ocr = PaddleOCR(
                use_angle_cls=settings.PPOCR_USE_ANGLE_CLS,
                lang=settings.PPOCR_LANG,
                use_gpu=settings.PPOCR_USE_GPU,
                det_model_dir=(
                    settings.PPOCR_DET_MODEL_DIR
                    if settings.PPOCR_DET_MODEL_DIR
                    else None
                ),
                rec_model_dir=(
                    settings.PPOCR_REC_MODEL_DIR
                    if settings.PPOCR_REC_MODEL_DIR
                    else None
                ),
                show_log=False,
            )

            self.enabled = True
            logger.info("✅ PPOCR 초기화 성공")

        except ImportError as e:
            logger.error(f"❌ PaddleOCR 모듈을 찾을 수 없습니다: {e}")
            logger.info("💡 설치 방법: pip install paddlepaddle paddleocr")

        except Exception as e:
            logger.error(f"❌ PPOCR 초기화 실패: {e}")

    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """이미지 전처리"""
        try:
            # 그레이스케일 변환
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image

            # 노이즈 제거
            denoised = cv2.medianBlur(gray, 3)

            # 대비 향상 (CLAHE 적용)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(denoised)

            # 이진화 (Otsu's method)
            _, binary = cv2.threshold(
                enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
            )

            return binary

        except Exception as e:
            logger.error(f"이미지 전처리 오류: {e}")
            return image

    def recognize_text(self, image_path: str, preprocess: bool = True) -> Dict:
        """이미지에서 텍스트 인식"""
        if not self.enabled:
            return {
                "success": False,
                "error": "PPOCR 서비스가 비활성화되어 있습니다.",
                "text_blocks": [],
            }

        try:
            # 이미지 로드
            if isinstance(image_path, str):
                image = cv2.imread(image_path)
                if image is None:
                    return {
                        "success": False,
                        "error": "이미지 파일을 읽을 수 없습니다.",
                        "text_blocks": [],
                    }
            else:
                image = image_path

            # 전처리 적용
            if preprocess:
                processed_image = self.preprocess_image(image)
            else:
                processed_image = image

            # OCR 수행
            result = self.ocr.ocr(processed_image, cls=True)

            if not result or not result[0]:
                return {
                    "success": True,
                    "message": "인식된 텍스트가 없습니다.",
                    "text_blocks": [],
                }

            # 결과 파싱
            text_blocks = []
            full_text = ""

            for line in result[0]:
                if line:
                    box = line[0]  # 좌표
                    text_info = line[1]  # (텍스트, 신뢰도)
                    text = text_info[0]
                    confidence = text_info[1]

                    # 좌표 정보 정리
                    coordinates = {
                        "top_left": box[0],
                        "top_right": box[1],
                        "bottom_right": box[2],
                        "bottom_left": box[3],
                    }

                    text_block = {
                        "text": text,
                        "confidence": round(confidence, 3),
                        "coordinates": coordinates,
                    }

                    text_blocks.append(text_block)
                    full_text += text + " "

            return {
                "success": True,
                "text_blocks": text_blocks,
                "full_text": full_text.strip(),
                "total_blocks": len(text_blocks),
                "average_confidence": (
                    round(
                        sum(block["confidence"] for block in text_blocks)
                        / len(text_blocks),
                        3,
                    )
                    if text_blocks
                    else 0
                ),
            }

        except Exception as e:
            logger.error(f"PPOCR 텍스트 인식 오류: {e}")
            return {
                "success": False,
                "error": f"텍스트 인식 중 오류가 발생했습니다: {str(e)}",
                "text_blocks": [],
            }

    def recognize_from_bytes(self, image_bytes: bytes, preprocess: bool = True) -> Dict:
        """바이트 데이터에서 텍스트 인식"""
        try:
            # 바이트를 numpy 배열로 변환
            nparr = np.frombuffer(image_bytes, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if image is None:
                return {
                    "success": False,
                    "error": "이미지 데이터를 디코딩할 수 없습니다.",
                    "text_blocks": [],
                }

            return self.recognize_text(image, preprocess)

        except Exception as e:
            logger.error(f"바이트 이미지 인식 오류: {e}")
            return {
                "success": False,
                "error": f"이미지 처리 중 오류가 발생했습니다: {str(e)}",
                "text_blocks": [],
            }

    def batch_recognize(
        self, image_paths: List[str], preprocess: bool = True
    ) -> List[Dict]:
        """여러 이미지 일괄 인식"""
        results = []

        for i, image_path in enumerate(image_paths):
            logger.info(f"배치 처리 중... ({i+1}/{len(image_paths)})")
            result = self.recognize_text(image_path, preprocess)
            result["image_path"] = image_path
            results.append(result)

        return results

    def extract_classical_chinese(self, text_blocks: List[Dict]) -> Dict:
        """한문(고전 중국어) 문자 추출 및 정리"""
        try:
            classical_chinese_blocks = []

            for block in text_blocks:
                text = block["text"]

                # 한문 문자 필터링 (기본적인 한자 범위)
                chinese_chars = ""
                for char in text:
                    # 한자 유니코드 범위 확인
                    if "\u4e00" <= char <= "\u9fff":
                        chinese_chars += char

                if chinese_chars:
                    classical_block = {
                        "original_text": text,
                        "classical_chinese": chinese_chars,
                        "confidence": block["confidence"],
                        "coordinates": block["coordinates"],
                        "char_count": len(chinese_chars),
                    }
                    classical_chinese_blocks.append(classical_block)

            return {
                "success": True,
                "classical_chinese_blocks": classical_chinese_blocks,
                "total_chinese_chars": sum(
                    block["char_count"] for block in classical_chinese_blocks
                ),
                "extraction_summary": f"{len(classical_chinese_blocks)}개 블록에서 한문 추출 완료",
            }

        except Exception as e:
            logger.error(f"한문 추출 오류: {e}")
            return {
                "success": False,
                "error": f"한문 추출 중 오류가 발생했습니다: {str(e)}",
                "classical_chinese_blocks": [],
            }

    def get_service_info(self) -> Dict:
        """서비스 정보 반환"""
        return {
            "service_name": "PPOCR Service",
            "version": "2.7+",
            "enabled": self.enabled,
            "supported_languages": ["ch", "en", "korean"],
            "features": [
                "텍스트 감지 및 인식",
                "방향 분류",
                "이미지 전처리",
                "한문 특화 처리",
                "배치 처리",
            ],
            "settings": {
                "use_gpu": settings.PPOCR_USE_GPU,
                "use_angle_cls": settings.PPOCR_USE_ANGLE_CLS,
                "language": settings.PPOCR_LANG,
            },
        }


# 전역 서비스 인스턴스
ppocr_service = PPOCRService()
