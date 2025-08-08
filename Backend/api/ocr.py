import os
import uuid
import tempfile
from dotenv import load_dotenv
from config.database import get_db

from models.ocr_model import OCRAnalysis
from services.ocr_service import analyze_document
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from fastapi.responses import FileResponse

from pydantic import BaseModel
from typing import List, Dict, Union, Any
from sqlalchemy.orm import Session

load_dotenv()
IS_DEBUG = os.getenv("IS_DEBUG", "")

router = APIRouter()


class OCRRequest(BaseModel):
    engine: str = "paddle"  # "paddle" or "azure"
    extract_text_only: bool = False
    visualization: bool = True


class OCRResponse(BaseModel):
    id: int
    analysis_id: str
    filename: str
    engine: str
    status: str
    extracted_text: str
    word_count: int
    confidence_score: float
    processing_time: float
    visualization_path: Union[str, None] = None
    timestamp: str
    ocr_data: Union[Dict[str, Any], None] = None


@router.post("/ocr/analyze", response_model=OCRResponse)
async def analyze_ocr(
    file: UploadFile = File(...),
    engine: str = "paddle",
    extract_text_only: bool = False,
    visualization: bool = True,
    db: Session = Depends(get_db)
):
    """
    OCR 문서 분석 처리
    """
    print(f"=== OCR 분석 요청 ===")
    print(f"파일명: {file.filename}")
    print(f"엔진: {engine}")
    print(f"텍스트만 추출: {extract_text_only}")
    print(f"시각화: {visualization}")

    # 파일 형식 검증
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="이미지 파일만 지원됩니다.")

    # 분석 ID 생성
    analysis_id = str(uuid.uuid4())

    try:
        # 업로드된 파일 임시 저장
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.filename}") as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name

        # OCR 분석 실행
        analysis_result = analyze_document(
            file_path=temp_file_path,
            engine=engine,
            extract_text_only=extract_text_only,
            visualization=visualization
        )

        # 임시 파일 정리
        os.unlink(temp_file_path)

        if IS_DEBUG:
            print(f"분석 결과: {analysis_result.status}")
            print(f"추출된 텍스트 길이: {len(analysis_result.extracted_text)}")
            print(f"신뢰도 점수: {analysis_result.confidence_score}")

        # OCR 분석 기록 저장 (결과와 함께)
        ocr_analysis = OCRAnalysis(
            analysis_id=analysis_id,
            filename=file.filename or "unknown",
            engine=engine,
            status=analysis_result.status,
            extracted_text=analysis_result.extracted_text,
            word_count=analysis_result.word_count,
            confidence_score=analysis_result.confidence_score,
            processing_time=analysis_result.processing_time,
            extract_text_only=extract_text_only,
            visualization_requested=visualization,
            visualization_path=analysis_result.visualization_path,
            error_message=analysis_result.error_message
        )
        db.add(ocr_analysis)
        db.commit()

        return OCRResponse(
            id=ocr_analysis.id,
            analysis_id=analysis_id,
            filename=file.filename,
            engine=engine,
            status=analysis_result.status,
            extracted_text=analysis_result.extracted_text,
            word_count=analysis_result.word_count,
            confidence_score=analysis_result.confidence_score,
            processing_time=analysis_result.processing_time,
            visualization_path=analysis_result.visualization_path,
            timestamp=ocr_analysis.created_at.isoformat(),
            ocr_data=analysis_result.ocr_data if not extract_text_only else None
        )

    except Exception as e:
        print(f"❌ OCR 분석 오류: {e}")
        # 임시 파일 정리 (에러 시)
        try:
            os.unlink(temp_file_path)
        except:
            pass
        
        # 실패한 분석 기록 저장
        try:
            failed_analysis = OCRAnalysis(
                analysis_id=analysis_id,
                filename=file.filename or "unknown",
                engine=engine,
                status="failed",
                extracted_text="",
                word_count=0,
                confidence_score=0.0,
                processing_time=0.0,
                extract_text_only=extract_text_only,
                visualization_requested=visualization,
                visualization_path=None,
                error_message=str(e)
            )
            db.add(failed_analysis)
            db.commit()
        except:
            pass

        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ocr/analysis/history/{analysis_id}")
async def get_analysis_history(analysis_id: str, db: Session = Depends(get_db)):
    """
    OCR 분석 기록 조회
    """
    try:
        analysis = (
            db.query(OCRAnalysis)
            .filter(OCRAnalysis.analysis_id == analysis_id)
            .first()
        )

        if not analysis:
            raise HTTPException(status_code=404, detail="분석 기록을 찾을 수 없습니다.")

        return analysis.to_dict()

    except Exception as e:
        print(f"❌ 분석 기록 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ocr/analysis/list")
async def get_analysis_list(
    limit: int = 20,
    offset: int = 0,
    engine: Union[str, None] = None,
    status: Union[str, None] = None,
    db: Session = Depends(get_db)
):
    """
    OCR 분석 목록 조회
    """
    try:
        query = db.query(OCRAnalysis)
        
        if engine:
            query = query.filter(OCRAnalysis.engine == engine)
        if status:
            query = query.filter(OCRAnalysis.status == status)

        analyses = (
            query.order_by(OCRAnalysis.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        return [analysis.to_dict() for analysis in analyses]

    except Exception as e:
        print(f"❌ 분석 목록 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ocr/visualization/{analysis_id}")
async def get_visualization(analysis_id: str, db: Session = Depends(get_db)):
    """
    OCR 분석 시각화 파일 조회
    """
    try:
        analysis = (
            db.query(OCRAnalysis)
            .filter(OCRAnalysis.analysis_id == analysis_id)
            .first()
        )

        if not analysis:
            raise HTTPException(status_code=404, detail="분석 기록을 찾을 수 없습니다.")

        analysis_dict = analysis.to_dict()
        viz_path = analysis_dict.get('visualization_path')
        
        if not viz_path or not os.path.exists(viz_path):
            raise HTTPException(status_code=404, detail="시각화 파일을 찾을 수 없습니다.")

        return FileResponse(
            viz_path,
            media_type="image/png",
            filename=f"viz_{analysis_id}.png"
        )

    except Exception as e:
        print(f"❌ 시각화 파일 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))