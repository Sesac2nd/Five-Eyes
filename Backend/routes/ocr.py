from fastapi import APIRouter, File, UploadFile, HTTPException, Form
from fastapi.responses import JSONResponse
from typing import Optional, List
import logging

from services.ppocr_service import ppocr_service
from services.azure_cognitive_service import azure_cognitive_service
from schemas.ocr import (
    OCRResponse,
    OCRComparisonResponse,
    HanjaExtractionResponse,
    OCRServiceInfo,
)
from utils.file_handler import validate_image_file

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/ppocr", response_model=OCRResponse)
async def recognize_with_ppocr(
    file: UploadFile = File(...), preprocess: bool = Form(True)
):
    """PPOCR을 사용한 한문 인식"""
    try:
        # 파일 검증
        if not validate_image_file(file):
            raise HTTPException(
                status_code=400, detail="지원하지 않는 이미지 형식입니다."
            )

        # 파일 읽기
        image_bytes = await file.read()

        if len(image_bytes) == 0:
            raise HTTPException(status_code=400, detail="빈 파일입니다.")

        logger.info(f"📖 PPOCR 요청: {file.filename} ({len(image_bytes)} bytes)")

        # PPOCR 인식 수행
        result = ppocr_service.recognize_from_bytes(image_bytes, preprocess)

        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["error"])

        # 한문 추출
        classical_chinese = ppocr_service.extract_classical_chinese(
            result["text_blocks"]
        )

        return OCRResponse(
            success=True,
            message="PPOCR 인식 완료",
            text_blocks=result["text_blocks"],
            full_text=result["full_text"],
            total_blocks=result["total_blocks"],
            average_confidence=result["average_confidence"],
            classical_chinese=classical_chinese,
            service_used="PPOCR",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ PPOCR 처리 오류: {e}")
        raise HTTPException(
            status_code=500, detail=f"PPOCR 처리 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/azure", response_model=OCRResponse)
async def recognize_with_azure(
    file: UploadFile = File(...), language: str = Form("zh-Hans")
):
    """Azure Cognitive Services를 사용한 한자 인식"""
    try:
        # 파일 검증
        if not validate_image_file(file):
            raise HTTPException(
                status_code=400, detail="지원하지 않는 이미지 형식입니다."
            )

        # 파일 읽기
        image_bytes = await file.read()

        if len(image_bytes) == 0:
            raise HTTPException(status_code=400, detail="빈 파일입니다.")

        logger.info(
            f"🧠 Azure OCR 요청: {file.filename} ({len(image_bytes)} bytes, 언어: {language})"
        )

        # Azure OCR 인식 수행
        if language in ["zh-Hans", "zh-Hant"]:
            result = azure_cognitive_service.recognize_chinese_text(image_bytes)
        else:
            result = azure_cognitive_service.recognize_text(image_bytes, language)

        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["error"])

        # 한자 추출
        hanja_extraction = azure_cognitive_service.extract_hanja_characters(
            result["text_blocks"]
        )

        return OCRResponse(
            success=True,
            message="Azure OCR 인식 완료",
            text_blocks=result["text_blocks"],
            full_text=result["full_text"],
            total_blocks=result["total_blocks"],
            average_confidence=0.8,  # Azure는 평균 신뢰도를 제공하지 않음
            classical_chinese=hanja_extraction,
            service_used="Azure Cognitive Services",
            language=result.get("language", language),
            orientation=result.get("orientation"),
            text_angle=result.get("text_angle"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Azure OCR 처리 오류: {e}")
        raise HTTPException(
            status_code=500, detail=f"Azure OCR 처리 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/compare", response_model=OCRComparisonResponse)
async def compare_ocr_results(
    file: UploadFile = File(...),
    preprocess: bool = Form(True),
    azure_language: str = Form("zh-Hans"),
):
    """PPOCR과 Azure OCR 결과 비교"""
    try:
        # 파일 검증
        if not validate_image_file(file):
            raise HTTPException(
                status_code=400, detail="지원하지 않는 이미지 형식입니다."
            )

        # 파일 읽기
        image_bytes = await file.read()

        if len(image_bytes) == 0:
            raise HTTPException(status_code=400, detail="빈 파일입니다.")

        logger.info(f"🔄 OCR 비교 요청: {file.filename} ({len(image_bytes)} bytes)")

        # PPOCR 인식
        ppocr_result = ppocr_service.recognize_from_bytes(image_bytes, preprocess)

        # Azure OCR 인식
        azure_result = azure_cognitive_service.recognize_chinese_text(image_bytes)

        # 결과 비교
        comparison = azure_cognitive_service.compare_with_ppocr(
            image_bytes, ppocr_result
        )

        return OCRComparisonResponse(
            success=True,
            message="OCR 비교 완료",
            ppocr_result={
                "success": ppocr_result["success"],
                "text_blocks": ppocr_result.get("text_blocks", []),
                "full_text": ppocr_result.get("full_text", ""),
                "total_blocks": ppocr_result.get("total_blocks", 0),
                "average_confidence": ppocr_result.get("average_confidence", 0),
            },
            azure_result={
                "success": azure_result["success"],
                "text_blocks": azure_result.get("text_blocks", []),
                "full_text": azure_result.get("full_text", ""),
                "total_blocks": azure_result.get("total_blocks", 0),
                "language": azure_result.get("language", azure_language),
            },
            comparison=comparison.get("comparison", {}),
            recommendation=comparison.get("comparison", {}).get("recommendation", ""),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ OCR 비교 처리 오류: {e}")
        raise HTTPException(
            status_code=500, detail=f"OCR 비교 처리 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/extract-hanja", response_model=HanjaExtractionResponse)
async def extract_hanja_only(
    file: UploadFile = File(...), method: str = Form("both")  # "ppocr", "azure", "both"
):
    """한자 문자만 추출"""
    try:
        # 파일 검증
        if not validate_image_file(file):
            raise HTTPException(
                status_code=400, detail="지원하지 않는 이미지 형식입니다."
            )

        # 파일 읽기
        image_bytes = await file.read()

        if len(image_bytes) == 0:
            raise HTTPException(status_code=400, detail="빈 파일입니다.")

        logger.info(f"🔍 한자 추출 요청: {file.filename} (방법: {method})")

        extracted_hanja = {}

        # PPOCR로 한자 추출
        if method in ["ppocr", "both"]:
            ppocr_result = ppocr_service.recognize_from_bytes(image_bytes, True)
            if ppocr_result["success"]:
                ppocr_hanja = ppocr_service.extract_classical_chinese(
                    ppocr_result["text_blocks"]
                )
                extracted_hanja["ppocr"] = ppocr_hanja

        # Azure로 한자 추출
        if method in ["azure", "both"]:
            azure_result = azure_cognitive_service.recognize_chinese_text(image_bytes)
            if azure_result["success"]:
                azure_hanja = azure_cognitive_service.extract_hanja_characters(
                    azure_result["text_blocks"]
                )
                extracted_hanja["azure"] = azure_hanja

        # 결합된 한자 목록 생성
        all_hanja_chars = set()

        for service_name, hanja_data in extracted_hanja.items():
            if hanja_data.get("success"):
                for block in hanja_data.get("hanja_blocks", []) or hanja_data.get(
                    "classical_chinese_blocks", []
                ):
                    hanja_text = block.get("hanja_text") or block.get(
                        "classical_chinese", ""
                    )
                    for char in hanja_text:
                        all_hanja_chars.add(char)

        return HanjaExtractionResponse(
            success=True,
            message=f"한자 추출 완료 ({method} 방법 사용)",
            extracted_hanja=extracted_hanja,
            unique_hanja_chars=list(all_hanja_chars),
            total_unique_chars=len(all_hanja_chars),
            extraction_method=method,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 한자 추출 처리 오류: {e}")
        raise HTTPException(
            status_code=500, detail=f"한자 추출 처리 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/batch-process")
async def batch_ocr_process(
    files: List[UploadFile] = File(...),
    method: str = Form("ppocr"),  # "ppocr", "azure", "both"
    preprocess: bool = Form(True),
):
    """여러 이미지 일괄 OCR 처리"""
    try:
        if len(files) > 10:
            raise HTTPException(
                status_code=400, detail="한 번에 최대 10개 파일까지 처리 가능합니다."
            )

        results = []

        for i, file in enumerate(files):
            logger.info(f"📄 배치 처리 중... ({i+1}/{len(files)}): {file.filename}")

            try:
                # 파일 검증
                if not validate_image_file(file):
                    results.append(
                        {
                            "filename": file.filename,
                            "success": False,
                            "error": "지원하지 않는 이미지 형식입니다.",
                        }
                    )
                    continue

                # 파일 읽기
                image_bytes = await file.read()

                if len(image_bytes) == 0:
                    results.append(
                        {
                            "filename": file.filename,
                            "success": False,
                            "error": "빈 파일입니다.",
                        }
                    )
                    continue

                # OCR 처리
                if method == "ppocr":
                    result = ppocr_service.recognize_from_bytes(image_bytes, preprocess)
                elif method == "azure":
                    result = azure_cognitive_service.recognize_chinese_text(image_bytes)
                elif method == "both":
                    ppocr_result = ppocr_service.recognize_from_bytes(
                        image_bytes, preprocess
                    )
                    azure_result = azure_cognitive_service.recognize_chinese_text(
                        image_bytes
                    )
                    result = {
                        "success": True,
                        "ppocr": ppocr_result,
                        "azure": azure_result,
                    }

                results.append(
                    {
                        "filename": file.filename,
                        "success": result["success"],
                        "result": result,
                        "file_size": len(image_bytes),
                    }
                )

            except Exception as file_error:
                logger.error(f"❌ 파일 처리 오류 ({file.filename}): {file_error}")
                results.append(
                    {
                        "filename": file.filename,
                        "success": False,
                        "error": str(file_error),
                    }
                )

        # 통계 계산
        successful_count = sum(1 for r in results if r["success"])
        failed_count = len(results) - successful_count

        return {
            "success": True,
            "message": f"배치 처리 완료: 성공 {successful_count}개, 실패 {failed_count}개",
            "results": results,
            "statistics": {
                "total_files": len(files),
                "successful": successful_count,
                "failed": failed_count,
                "method_used": method,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 배치 처리 오류: {e}")
        raise HTTPException(
            status_code=500, detail=f"배치 처리 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/service-info", response_model=OCRServiceInfo)
async def get_ocr_service_info():
    """OCR 서비스 정보 조회"""
    try:
        ppocr_info = ppocr_service.get_service_info()
        azure_info = azure_cognitive_service.get_service_info()

        return OCRServiceInfo(
            ppocr_service=ppocr_info,
            azure_service=azure_info,
            available_services=[
                service
                for service, info in [
                    ("PPOCR", ppocr_info),
                    ("Azure Cognitive Services", azure_info),
                ]
                if info.get("enabled", False)
            ],
            supported_formats=["jpg", "jpeg", "png", "bmp", "tiff"],
            max_file_size="10MB",
        )

    except Exception as e:
        logger.error(f"❌ 서비스 정보 조회 오류: {e}")
        raise HTTPException(
            status_code=500, detail="서비스 정보 조회 중 오류가 발생했습니다."
        )


@router.get("/health")
async def ocr_health_check():
    """OCR 서비스 상태 확인"""
    return {
        "status": "healthy",
        "services": {
            "ppocr": ppocr_service.enabled,
            "azure_cognitive": azure_cognitive_service.enabled,
        },
        "capabilities": ["한문/한자 인식", "다중 엔진 비교", "배치 처리", "한자 추출"],
        "authentication": "disabled",
    }
