# services/paddle_ocr_service.py
import os
import time
import logging
import numpy as np
from typing import List, Dict, Optional
from utils.image_processing import ImageProcessor
from utils.text_processing import HistoricalDocumentTextProcessor
from models.ocr import WordResult, LineResult

logger = logging.getLogger(__name__)


class PaddleOCRService:
    """PaddleOCR 서비스 - 한문 특화"""

    def __init__(self):
        self.ocr = None
        self.enabled = False
        self._initialize_paddle_ocr()

    def _initialize_paddle_ocr(self):
        """PaddleOCR 초기화"""
        try:
            # PaddleOCR 임포트 (지연 로딩)
            import paddle
            from paddleocr import PaddleOCR

            # 메모리 최적화 설정
            paddle.set_flags(
                {
                    "FLAGS_fraction_of_cpu_memory_to_use": 0.5,
                    "FLAGS_eager_delete_tensor_gb": 0.0,
                    "FLAGS_fast_eager_deletion_mode": True,
                    "FLAGS_use_mkldnn": False,
                }
            )

            try:
                # 고성능 모드로 먼저 시도
                self.ocr = PaddleOCR(
                    lang="chinese_cht",  # 중국어 번체 (한자)
                    text_det_limit_side_len=1500,
                    text_det_limit_type="max",
                    cpu_threads=1,
                    use_doc_orientation_classify=True,
                    use_doc_unwarping=False,
                    use_textline_orientation=False,
                    enable_mkldnn=False,
                    ocr_version="PP-OCRv5",
                    enable_hpi=True,  # 고성능 추론
                )
                logger.info("✅ PaddleOCR 고성능 모드 초기화 성공")

            except RuntimeError as e:
                logger.warning(f"고성능 모드 실패, 일반 모드로 재시도: {e}")
                # 일반 모드로 폴백
                self.ocr = PaddleOCR(
                    lang="chinese_cht",
                    text_det_limit_side_len=1500,
                    text_det_limit_type="max",
                    cpu_threads=1,
                    use_doc_orientation_classify=True,
                    use_doc_unwarping=False,
                    use_textline_orientation=True,
                    enable_mkldnn=False,
                    ocr_version="PP-OCRv5",
                    enable_hpi=False,  # 고성능 비활성화
                    text_det_box_thresh=0.7,
                    precision="fp32",
                )
                logger.info("✅ PaddleOCR 일반 모드 초기화 성공")

            self.enabled = True

        except ImportError as e:
            logger.error(f"PaddleOCR 라이브러리가 설치되지 않음: {e}")
            self.enabled = False
        except Exception as e:
            logger.error(f"PaddleOCR 초기화 실패: {e}")
            self.enabled = False

    def is_available(self) -> bool:
        """서비스 사용 가능 여부"""
        return self.enabled and self.ocr is not None

    def process_image(self, image_data: bytes) -> Dict:
        """이미지 OCR 처리 메인 함수"""
        if not self.is_available():
            return {
                "success": False,
                "error": "PaddleOCR 서비스가 비활성화되어 있습니다.",
                "processing_time": 0.0,
            }

        start_time = time.time()
        temp_file_path = None

        try:
            # 1. 이미지 전처리
            logger.info("🔄 PaddleOCR용 이미지 전처리 시작")
            processed_image = ImageProcessor.enhance_image_for_ocr(image_data, "ppocr")

            # 2. 임시 파일 생성
            temp_file_path = ImageProcessor.save_temp_file(processed_image)
            logger.info(f"📁 임시 파일 생성: {temp_file_path}")

            # 3. PaddleOCR 실행
            logger.info("🔍 PaddleOCR 분석 시작")
            result = self.ocr.predict(input=temp_file_path)

            # 4. 결과 처리
            if not result:
                return {
                    "success": False,
                    "error": "PaddleOCR에서 결과를 반환하지 않았습니다.",
                    "processing_time": time.time() - start_time,
                }

            # 5. 결과 파싱 및 정렬
            processed_result = self._process_paddle_result(
                result[0] if result else None
            )

            processing_time = time.time() - start_time
            logger.info(f"✅ PaddleOCR 처리 완료 ({processing_time:.2f}초)")

            return {
                "success": True,
                "processing_time": processing_time,
                **processed_result,
            }

        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"❌ PaddleOCR 처리 실패: {e}")
            return {
                "success": False,
                "error": f"PaddleOCR 처리 중 오류: {str(e)}",
                "processing_time": processing_time,
            }

        finally:
            # 임시 파일 정리
            if temp_file_path:
                ImageProcessor.cleanup_temp_file(temp_file_path)

    def _process_paddle_result(self, paddle_result) -> Dict:
        """PaddleOCR 결과를 통일된 형태로 변환"""
        if not paddle_result:
            return {
                "lines": [],
                "full_text": "",
                "word_count": 0,
                "confidence_avg": 0.0,
            }

        try:
            # PaddleOCR 결과에서 단어 정보 추출
            words_data = []

            # PaddleOCR 결과 구조: [[[bbox], (text, confidence)], ...]
            for item in paddle_result:
                if len(item) >= 2:
                    bbox_points = item[0]  # [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
                    text_info = item[1]  # (text, confidence)

                    if len(text_info) >= 2:
                        text = text_info[0]
                        confidence = float(text_info[1])

                        # bbox 점들을 평면화하여 polygon 형태로 변환
                        polygon = []
                        min_x, min_y = float("inf"), float("inf")
                        max_x, max_y = float("-inf"), float("-inf")

                        for point in bbox_points:
                            x, y = float(point[0]), float(point[1])
                            polygon.extend([x, y])
                            min_x, min_y = min(min_x, x), min(min_y, y)
                            max_x, max_y = max(max_x, x), max(max_y, y)

                        # 중심점 계산
                        center_x = (min_x + max_x) / 2
                        center_y = (min_y + max_y) / 2

                        words_data.append(
                            {
                                "text": text,
                                "confidence": confidence,
                                "polygon": polygon,
                                "bbox": [
                                    int(min_x),
                                    int(min_y),
                                    int(max_x - min_x),
                                    int(max_y - min_y),
                                ],
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
                all_bboxes = [w["bbox"] for w in line_words]
                min_x = min(bbox[0] for bbox in all_bboxes)
                min_y = min(bbox[1] for bbox in all_bboxes)
                max_x = max(bbox[0] + bbox[2] for bbox in all_bboxes)
                max_y = max(bbox[1] + bbox[3] for bbox in all_bboxes)

                line_bbox = [min_x, min_y, max_x - min_x, max_y - min_y]

                # WordResult 객체들 생성
                word_results = []
                for word in line_words:
                    word_result = WordResult(
                        text=word["text"],
                        confidence=word["confidence"],
                        bbox=word["bbox"],
                        polygon=word["polygon"],
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
            logger.error(f"PaddleOCR 결과 처리 실패: {e}")
            return {
                "lines": [],
                "full_text": "",
                "word_count": 0,
                "confidence_avg": 0.0,
            }


# 전역 인스턴스
paddle_ocr_service = PaddleOCRService()
