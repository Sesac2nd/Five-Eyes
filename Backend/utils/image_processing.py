import os
import tempfile
from PIL import Image
import io
import logging

logger = logging.getLogger(__name__)


class ImageProcessor:
    """이미지 전처리 클래스 (간단 버전)"""

    @staticmethod
    def validate_image(image_data: bytes) -> bool:
        """이미지 유효성 검사"""
        try:
            image = Image.open(io.BytesIO(image_data))
            if image.size[0] < 100 or image.size[1] < 100:
                return False
            if image.size[0] > 10000 or image.size[1] > 10000:
                return False
            return True
        except Exception as e:
            logger.error(f"이미지 유효성 검사 실패: {e}")
            return False

    @staticmethod
    def enhance_image_for_ocr(image_data: bytes, model_type: str = "azure") -> bytes:
        """OCR을 위한 이미지 향상 (기본 처리만)"""
        try:
            image = Image.open(io.BytesIO(image_data))

            # RGB 변환 (필요시)
            if image.mode not in ["RGB", "L"]:
                image = image.convert("RGB")

            # 바이트로 변환하여 반환
            output = io.BytesIO()
            image.save(output, format="PNG", quality=95)
            return output.getvalue()

        except Exception as e:
            logger.error(f"이미지 향상 실패: {e}")
            return image_data  # 원본 반환

    @staticmethod
    def resize_if_needed(image_data: bytes, max_size: int = 4096) -> bytes:
        """필요시 이미지 크기 조정"""
        try:
            image = Image.open(io.BytesIO(image_data))
            width, height = image.size

            # 최대 크기 체크
            if max(width, height) > max_size:
                # 비율 유지하면서 리사이즈
                ratio = max_size / max(width, height)
                new_width = int(width * ratio)
                new_height = int(height * ratio)

                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                logger.info(
                    f"이미지 리사이즈: {width}x{height} -> {new_width}x{new_height}"
                )

            # 바이트로 변환하여 반환
            output = io.BytesIO()
            image.save(output, format="PNG", quality=95)
            return output.getvalue()

        except Exception as e:
            logger.error(f"이미지 리사이즈 실패: {e}")
            return image_data  # 원본 반환

    @staticmethod
    def save_temp_file(image_data: bytes, suffix: str = ".png") -> str:
        """임시 파일로 저장"""
        try:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
            temp_file.write(image_data)
            temp_file.close()
            return temp_file.name
        except Exception as e:
            logger.error(f"임시 파일 생성 실패: {e}")
            raise

    @staticmethod
    def cleanup_temp_file(file_path: str):
        """임시 파일 정리"""
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
        except Exception as e:
            logger.warning(f"임시 파일 삭제 실패: {e}")


def preprocess_image_for_ocr(image_data: bytes, model_type: str) -> bytes:
    """OCR을 위한 통합 이미지 전처리"""
    processor = ImageProcessor()

    # 1. 유효성 검사
    if not processor.validate_image(image_data):
        raise ValueError("유효하지 않은 이미지입니다")

    # 2. 크기 조정
    image_data = processor.resize_if_needed(image_data)

    # 3. OCR 향상
    image_data = processor.enhance_image_for_ocr(image_data, model_type)

    return image_data
