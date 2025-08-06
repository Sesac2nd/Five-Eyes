from typing import List, Dict, Tuple
import logging

logger = logging.getLogger(__name__)


class HistoricalDocumentTextProcessor:
    """역사문서 전용 텍스트 처리 클래스 (간단 버전)"""

    @staticmethod
    def sort_words_vertical_reading(
        words_data: List[Dict], debug: bool = False
    ) -> List[str]:
        """고문서 OCR 결과를 세로줄 기준으로 정렬 (간단 버전)"""
        if not words_data:
            return []

        try:
            # 간단한 X 좌표 기준 정렬 (우→좌)
            sorted_words = sorted(
                words_data, key=lambda w: w.get("center_x", 0), reverse=True
            )
            return [word.get("text", "") for word in sorted_words]

        except Exception as e:
            logger.error(f"텍스트 정렬 실패: {e}")
            return [word.get("text", "") for word in words_data]

    @staticmethod
    def calculate_confidence_stats(words_data: List[Dict]) -> Dict:
        """신뢰도 통계 계산"""
        if not words_data:
            return {"avg": 0, "min": 0, "max": 0, "std": 0, "count": 0}

        confidences = []
        for word in words_data:
            conf = word.get("confidence", 1.0)
            if conf is not None:
                confidences.append(float(conf))

        if not confidences:
            return {"avg": 0, "min": 0, "max": 0, "std": 0, "count": 0}

        avg = sum(confidences) / len(confidences)
        return {
            "avg": avg,
            "min": min(confidences),
            "max": max(confidences),
            "std": 0,  # 간단 버전에서는 계산 생략
            "count": len(confidences),
        }


def process_ocr_text_historical(
    words_data: List[Dict], debug: bool = False
) -> Tuple[List[str], Dict]:
    """역사문서 OCR 텍스트 통합 처리"""
    processor = HistoricalDocumentTextProcessor()

    # 정렬된 텍스트
    sorted_texts = processor.sort_words_vertical_reading(words_data, debug)

    # 통계 정보
    stats = processor.calculate_confidence_stats(words_data)

    return sorted_texts, stats
