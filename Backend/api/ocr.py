# api/ocr.py
import uuid
import time
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from sqlalchemy.orm import Session
from typing import Optional
import logging

from config.database import get_db
from models.ocr import OCRLog, OCRRequest, OCRResult, OCRResponse, OCRModelType
from services.paddle_ocr_service import paddle_ocr_service
from services.azure_ocr_service import azure_ocr_service
from utils.image_processing import preprocess_image_for_ocr

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/ocr", response_model=OCRResponse)
async def process_ocr(
    file: UploadFile = File(..., description="분석할 이미지 파일"),
    model_type: str = Form(..., description="OCR 모델 타입 (ppocr 또는 azure)"),
    session_id: Optional[str] = Form(None, description="세션 ID (선택사항)"),
    db: Session = Depends(get_db),
):
    """
    이미지 OCR 처리 API

    - **file**: 업로드할 이미지 파일 (JPG, PNG, GIF 지원)
    - **model_type**: 사용할 OCR 모델 ("ppocr" 또는 "azure")
    - **session_id**: 세션 식별자 (선택사항, 없으면 자동 생성)
    """

    # 세션 ID 생성 (없는 경우)
    if not session_id:
        session_id = str(uuid.uuid4())

    # 모델 타입 검증
    try:
        model_enum = OCRModelType(model_type.lower())
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"지원하지 않는 모델 타입입니다. 'ppocr' 또는 'azure'를 사용하세요.",
        )

    # 파일 타입 검증
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="이미지 파일만 업로드 가능합니다.")

    start_time = time.time()
    ocr_log = None

    try:
        # 이미지 데이터 읽기
        logger.info(f"📁 파일 업로드: {file.filename} ({file.content_type})")
        image_data = await file.read()
        file_size = len(image_data)

        # 파일 크기 검증 (최대 10MB)
        if file_size > 10 * 1024 * 1024:
            raise HTTPException(
                status_code=413,
                detail="파일 크기가 너무 큽니다. 최대 10MB까지 지원합니다.",
            )

        # OCR 로그 초기 생성
        ocr_log = OCRLog(
            session_id=session_id,
            model_type=model_enum.value,
            original_filename=file.filename,
            file_size=file_size,
            success=False,
        )
        db.add(ocr_log)
        db.flush()  # ID 생성을 위해

        # 이미지 전처리
        logger.info(f"🔄 이미지 전처리 시작 (모델: {model_enum.value})")
        try:
            processed_image_data = preprocess_image_for_ocr(
                image_data, model_enum.value
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"이미지 전처리 실패: {e}")
            processed_image_data = image_data  # 원본 사용

        # 선택된 모델로 OCR 처리
        logger.info(f"🤖 OCR 처리 시작 (모델: {model_enum.value})")

        if model_enum == OCRModelType.PPOCR:
            if not paddle_ocr_service.is_available():
                raise HTTPException(
                    status_code=503,
                    detail="PaddleOCR 서비스가 현재 사용할 수 없습니다. 서버 관리자에게 문의하세요.",
                )
            ocr_result_dict = paddle_ocr_service.process_image(processed_image_data)

        elif model_enum == OCRModelType.AZURE:
            if not azure_ocr_service.is_available():
                raise HTTPException(
                    status_code=503,
                    detail="Azure OCR 서비스가 현재 사용할 수 없습니다. API 키 설정을 확인하세요.",
                )
            ocr_result_dict = azure_ocr_service.process_image(processed_image_data)

        else:
            raise HTTPException(status_code=400, detail="지원하지 않는 모델입니다.")

        # OCR 결과 처리
        total_processing_time = time.time() - start_time

        if ocr_result_dict["success"]:
            # 성공적인 결과 처리
            ocr_result = OCRResult(
                success=True,
                model_type=model_enum.value,
                processing_time=total_processing_time,
                confidence_avg=ocr_result_dict.get("confidence_avg"),
                word_count=ocr_result_dict.get("word_count"),
                lines=ocr_result_dict.get("lines"),
                full_text=ocr_result_dict.get("full_text"),
            )

            # 로그 업데이트
            ocr_log.success = True
            ocr_log.processing_time = total_processing_time
            ocr_log.confidence_avg = ocr_result_dict.get("confidence_avg")
            ocr_log.word_count = ocr_result_dict.get("word_count")
            ocr_log.result_data = ocr_result_dict

            logger.info(
                f"✅ OCR 처리 성공: {ocr_result.word_count}개 단어, 평균 신뢰도 {ocr_result.confidence_avg:.3f}"
            )

        else:
            # 실패한 결과 처리
            error_message = ocr_result_dict.get("error", "알 수 없는 오류")

            ocr_result = OCRResult(
                success=False,
                model_type=model_enum.value,
                processing_time=total_processing_time,
                error_message=error_message,
            )

            # 로그 업데이트
            ocr_log.success = False
            ocr_log.processing_time = total_processing_time
            ocr_log.error_message = error_message

            logger.error(f"❌ OCR 처리 실패: {error_message}")

        # 데이터베이스 커밋
        db.commit()

        # 응답 생성
        response = OCRResponse(
            log_id=ocr_log.id, session_id=session_id, result=ocr_result
        )

        return response

    except HTTPException:
        # FastAPI HTTPException은 그대로 전파
        if ocr_log:
            db.rollback()
        raise

    except Exception as e:
        # 예상치 못한 오류 처리
        logger.error(f"❌ OCR API 예외 발생: {e}")

        if ocr_log:
            ocr_log.success = False
            ocr_log.processing_time = time.time() - start_time
            ocr_log.error_message = str(e)
            try:
                db.commit()
            except:
                db.rollback()

        raise HTTPException(
            status_code=500, detail=f"서버 내부 오류가 발생했습니다: {str(e)}"
        )


@router.get("/ocr/history/{session_id}")
async def get_ocr_history(session_id: str, db: Session = Depends(get_db)):
    """
    특정 세션의 OCR 처리 기록 조회
    """
    try:
        logs = (
            db.query(OCRLog)
            .filter(OCRLog.session_id == session_id)
            .order_by(OCRLog.created_at.desc())
            .all()
        )

        return {
            "session_id": session_id,
            "total_count": len(logs),
            "logs": [log.to_dict() for log in logs],
        }

    except Exception as e:
        logger.error(f"OCR 기록 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ocr/status")
async def get_ocr_status():
    """
    OCR 서비스 상태 확인
    """
    return {
        "paddle_ocr": {
            "available": paddle_ocr_service.is_available(),
            "status": (
                "✅ 사용 가능" if paddle_ocr_service.is_available() else "❌ 사용 불가"
            ),
        },
        "azure_ocr": {
            "available": azure_ocr_service.is_available(),
            "status": (
                "✅ 사용 가능" if azure_ocr_service.is_available() else "❌ 사용 불가"
            ),
        },
        "supported_models": ["ppocr", "azure"],
        "max_file_size": "10MB",
        "supported_formats": ["JPG", "PNG", "GIF"],
    }
