import os
import uuid
import shutil
from pathlib import Path
from typing import Optional, List, Dict
from fastapi import UploadFile, HTTPException
import magic
import logging

from config.settings import settings

logger = logging.getLogger(__name__)


def validate_image_file(file: UploadFile) -> bool:
    """이미지 파일 유효성 검사"""
    try:
        # 파일 확장자 검사
        file_extension = Path(file.filename).suffix.lower()
        if file_extension not in settings.ALLOWED_IMAGE_EXTENSIONS:
            return False

        # 파일 크기 검사 (헤더만으로는 정확하지 않을 수 있음)
        if hasattr(file, "size") and file.size > settings.MAX_FILE_SIZE:
            return False

        # MIME 타입 검사 (content_type 확인)
        allowed_mime_types = [
            "image/jpeg",
            "image/jpg",
            "image/png",
            "image/bmp",
            "image/tiff",
            "image/tif",
        ]

        if file.content_type not in allowed_mime_types:
            return False

        return True

    except Exception as e:
        logger.error(f"이미지 파일 검증 오류: {e}")
        return False


def validate_audio_file(file: UploadFile) -> bool:
    """오디오 파일 유효성 검사"""
    try:
        # 파일 확장자 검사
        file_extension = Path(file.filename).suffix.lower()
        if file_extension not in settings.ALLOWED_AUDIO_EXTENSIONS:
            return False

        # 파일 크기 검사
        if hasattr(file, "size") and file.size > settings.MAX_FILE_SIZE:
            return False

        # MIME 타입 검사
        allowed_mime_types = [
            "audio/wav",
            "audio/wave",
            "audio/mpeg",
            "audio/mp3",
            "audio/m4a",
            "audio/ogg",
            "audio/webm",
        ]

        if file.content_type and file.content_type not in allowed_mime_types:
            return False

        return True

    except Exception as e:
        logger.error(f"오디오 파일 검증 오류: {e}")
        return False


def get_file_info(file: UploadFile) -> Dict:
    """파일 정보 추출"""
    try:
        file_info = {
            "filename": file.filename,
            "content_type": file.content_type,
            "extension": Path(file.filename).suffix.lower() if file.filename else "",
            "size": getattr(file, "size", 0),
        }

        return file_info

    except Exception as e:
        logger.error(f"파일 정보 추출 오류: {e}")
        return {}


def save_uploaded_file(file: UploadFile, upload_dir: str = "uploads") -> str:
    """업로드된 파일 저장"""
    try:
        # 업로드 디렉토리 생성
        upload_path = Path(upload_dir)
        upload_path.mkdir(parents=True, exist_ok=True)

        # 고유한 파일명 생성
        file_extension = Path(file.filename).suffix.lower()
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = upload_path / unique_filename

        # 파일 저장
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        logger.info(f"파일 저장 완료: {file_path}")
        return str(file_path)

    except Exception as e:
        logger.error(f"파일 저장 오류: {e}")
        raise HTTPException(status_code=500, detail=f"파일 저장 실패: {str(e)}")


def save_file_from_bytes(
    file_bytes: bytes, filename: str, upload_dir: str = "uploads"
) -> str:
    """바이트 데이터를 파일로 저장"""
    try:
        # 업로드 디렉토리 생성
        upload_path = Path(upload_dir)
        upload_path.mkdir(parents=True, exist_ok=True)

        # 고유한 파일명 생성
        file_extension = Path(filename).suffix.lower()
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = upload_path / unique_filename

        # 파일 저장
        with open(file_path, "wb") as f:
            f.write(file_bytes)

        logger.info(f"바이트 파일 저장 완료: {file_path}")
        return str(file_path)

    except Exception as e:
        logger.error(f"바이트 파일 저장 오류: {e}")
        raise HTTPException(status_code=500, detail=f"파일 저장 실패: {str(e)}")


def delete_file(file_path: str) -> bool:
    """파일 삭제"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"파일 삭제 완료: {file_path}")
            return True
        else:
            logger.warning(f"삭제할 파일이 존재하지 않음: {file_path}")
            return False

    except Exception as e:
        logger.error(f"파일 삭제 오류: {e}")
        return False


def cleanup_old_files(directory: str, max_age_hours: int = 24) -> int:
    """오래된 파일 정리"""
    try:
        import time

        if not os.path.exists(directory):
            return 0

        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        deleted_count = 0

        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)

            if os.path.isfile(file_path):
                file_age = current_time - os.path.getctime(file_path)

                if file_age > max_age_seconds:
                    if delete_file(file_path):
                        deleted_count += 1

        if deleted_count > 0:
            logger.info(f"오래된 파일 {deleted_count}개 정리 완료")

        return deleted_count

    except Exception as e:
        logger.error(f"파일 정리 오류: {e}")
        return 0


def get_file_mime_type(file_path: str) -> Optional[str]:
    """파일의 실제 MIME 타입 검사"""
    try:
        mime = magic.Magic(mime=True)
        return mime.from_file(file_path)

    except Exception as e:
        logger.error(f"MIME 타입 검사 오류: {e}")
        return None


def validate_file_content(file_path: str, expected_type: str) -> bool:
    """파일 내용 검증"""
    try:
        actual_mime = get_file_mime_type(file_path)

        if not actual_mime:
            return False

        # 이미지 파일 검증
        if expected_type == "image":
            return actual_mime.startswith("image/")

        # 오디오 파일 검증
        elif expected_type == "audio":
            return actual_mime.startswith("audio/")

        # 텍스트 파일 검증
        elif expected_type == "text":
            return actual_mime.startswith("text/") or actual_mime == "application/xml"

        return False

    except Exception as e:
        logger.error(f"파일 내용 검증 오류: {e}")
        return False


def create_thumbnail(
    image_path: str, thumbnail_size: tuple = (200, 200)
) -> Optional[str]:
    """이미지 썸네일 생성"""
    try:
        from PIL import Image

        # 원본 이미지 열기
        with Image.open(image_path) as img:
            # 썸네일 생성
            img.thumbnail(thumbnail_size, Image.Resampling.LANCZOS)

            # 썸네일 파일 경로
            file_path = Path(image_path)
            thumbnail_path = (
                file_path.parent / f"{file_path.stem}_thumb{file_path.suffix}"
            )

            # 썸네일 저장
            img.save(thumbnail_path, optimize=True, quality=85)

            logger.info(f"썸네일 생성 완료: {thumbnail_path}")
            return str(thumbnail_path)

    except ImportError:
        logger.warning("PIL(Pillow)가 설치되지 않아 썸네일을 생성할 수 없습니다.")
        return None
    except Exception as e:
        logger.error(f"썸네일 생성 오류: {e}")
        return None


def batch_file_operations(file_paths: List[str], operation: str) -> Dict:
    """배치 파일 작업"""
    try:
        results = []
        success_count = 0
        error_count = 0

        for file_path in file_paths:
            try:
                if operation == "delete":
                    success = delete_file(file_path)
                elif operation == "validate_image":
                    success = validate_file_content(file_path, "image")
                elif operation == "validate_audio":
                    success = validate_file_content(file_path, "audio")
                elif operation == "thumbnail":
                    thumbnail_path = create_thumbnail(file_path)
                    success = thumbnail_path is not None
                else:
                    success = False

                if success:
                    success_count += 1
                else:
                    error_count += 1

                results.append(
                    {"file_path": file_path, "success": success, "operation": operation}
                )

            except Exception as e:
                error_count += 1
                results.append(
                    {
                        "file_path": file_path,
                        "success": False,
                        "operation": operation,
                        "error": str(e),
                    }
                )

        return {
            "success": True,
            "total_files": len(file_paths),
            "success_count": success_count,
            "error_count": error_count,
            "results": results,
        }

    except Exception as e:
        logger.error(f"배치 파일 작업 오류: {e}")
        return {"success": False, "error": str(e), "results": []}


def get_storage_info(directory: str = "uploads") -> Dict:
    """저장소 정보 조회"""
    try:
        if not os.path.exists(directory):
            return {"exists": False, "total_files": 0, "total_size": 0}

        total_files = 0
        total_size = 0
        file_types = {}

        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                file_size = os.path.getsize(file_path)
                file_ext = Path(file).suffix.lower()

                total_files += 1
                total_size += file_size

                if file_ext in file_types:
                    file_types[file_ext] += 1
                else:
                    file_types[file_ext] = 1

        return {
            "exists": True,
            "directory": directory,
            "total_files": total_files,
            "total_size": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "file_types": file_types,
        }

    except Exception as e:
        logger.error(f"저장소 정보 조회 오류: {e}")
        return {"exists": False, "error": str(e)}
