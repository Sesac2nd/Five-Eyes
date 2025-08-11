# Backend/api/ocr.py - 상태 업데이트 수정된 버전
import os
import uuid
import tempfile
import threading
from datetime import datetime
from dotenv import load_dotenv
from config.database import get_db, SessionLocal

from models.ocr_model import OCRAnalysis
from services.ocr_service import analyze_document
from fastapi import (
    APIRouter,
    HTTPException,
    Depends,
    UploadFile,
    File,
    Form,
    BackgroundTasks,
)
from fastapi.responses import FileResponse, JSONResponse

from pydantic import BaseModel
from typing import List, Dict, Union, Any, Optional
from sqlalchemy.orm import Session

load_dotenv()
IS_DEBUG = os.getenv("IS_DEBUG", "")

router = APIRouter()

# 진행 중인 분석 상태 저장 (Redis 사용 가능하면 사용, 아니면 메모리)
try:
    import redis

    redis_client = redis.Redis.from_url(
        os.getenv("REDIS_URL", "redis://localhost:6379")
    )
    redis_client.ping()  # 연결 테스트
    USE_REDIS = True
    print("✅ Redis 연결 성공 - 상태 저장에 Redis 사용")
except:
    USE_REDIS = False
    ANALYSIS_STATUS = {}  # 메모리 저장소
    print("⚠️ Redis 연결 실패 - 메모리 저장소 사용")


# 비동기 모델들만 유지
class OCRAsyncResponse(BaseModel):
    analysis_id: str
    status: str
    message: str
    estimated_time: str


class OCRStatusResponse(BaseModel):
    analysis_id: str
    status: str
    progress_percentage: int = 0
    current_step: Optional[str] = None
    error_message: Optional[str] = None


def set_analysis_status(analysis_id: str, data: dict):
    """분석 상태 저장 (Redis 또는 메모리)"""
    if USE_REDIS:
        try:
            import json

            redis_client.setex(
                f"ocr_status:{analysis_id}", 3600, json.dumps(data)
            )  # 1시간 TTL
        except:
            ANALYSIS_STATUS[analysis_id] = data
    else:
        ANALYSIS_STATUS[analysis_id] = data


def get_analysis_status(analysis_id: str) -> dict:
    """분석 상태 조회"""
    if USE_REDIS:
        try:
            import json

            data = redis_client.get(f"ocr_status:{analysis_id}")
            return json.loads(data.decode()) if data else {}
        except:
            return ANALYSIS_STATUS.get(analysis_id, {})
    else:
        return ANALYSIS_STATUS.get(analysis_id, {})


def update_analysis_progress(analysis_id: str, progress: int, step: str):
    """분석 진행상태 업데이트 (개선된 버전)"""
    try:
        # 상태 저장
        set_analysis_status(
            analysis_id,
            {
                "progress": progress,
                "step": step,
                "status": "processing",
                "updated_at": datetime.now().isoformat(),
            },
        )

        # DB 업데이트 (별도 세션 사용)
        db = SessionLocal()
        try:
            analysis = (
                db.query(OCRAnalysis)
                .filter(OCRAnalysis.analysis_id == analysis_id)
                .first()
            )
            if analysis:
                analysis.status = "processing"
                if hasattr(analysis, "progress_percentage"):
                    analysis.progress_percentage = progress
                if hasattr(analysis, "current_step"):
                    analysis.current_step = step
                db.commit()
        finally:
            db.close()

        if IS_DEBUG:
            print(f"📊 진행상태 업데이트: {analysis_id} - {progress}% ({step})")
    except Exception as e:
        print(f"❌ 진행상태 업데이트 실패: {e}")


def background_ocr_analysis_thread(
    analysis_id: str,
    file_path: str,
    filename: str,
    engine: str,
    extract_text_only: bool,
    visualization: bool,
):
    """스레드로 실행되는 OCR 분석 (상태 업데이트 개선)"""
    try:
        print(f"🔍 백그라운드 OCR 분석 시작: {analysis_id}")

        # 1. 분석 시작
        update_analysis_progress(analysis_id, 5, "분석 초기화 중")

        # 2. 파일 전처리
        update_analysis_progress(analysis_id, 15, "이미지 전처리 중")

        # 3. OCR 엔진별 처리
        if engine == "paddle":
            update_analysis_progress(analysis_id, 25, "PaddleOCR 모델 로딩 중")
            import time

            time.sleep(2)  # 실제 모델 로딩 시간

            update_analysis_progress(analysis_id, 40, "한문 텍스트 검출 중")
            time.sleep(1)

            update_analysis_progress(analysis_id, 60, "텍스트 인식 및 분류 중")
            time.sleep(1)

            update_analysis_progress(analysis_id, 75, "텍스트 정렬 및 후처리 중")
        else:
            update_analysis_progress(analysis_id, 30, "Azure OCR 요청 중")
            update_analysis_progress(analysis_id, 60, "텍스트 추출 중")

        # 4. 실제 OCR 분석 실행
        update_analysis_progress(analysis_id, 80, "OCR 분석 실행 중")
        analysis_result = analyze_document(
            file_path=file_path,
            engine=engine,
            extract_text_only=extract_text_only,
            visualization=visualization,
        )

        # 5. 결과 저장
        update_analysis_progress(analysis_id, 90, "결과 저장 중")

        # DB 업데이트
        db = SessionLocal()
        try:
            analysis = (
                db.query(OCRAnalysis)
                .filter(OCRAnalysis.analysis_id == analysis_id)
                .first()
            )
            if analysis:
                analysis.status = analysis_result.status
                analysis.extracted_text = analysis_result.extracted_text
                analysis.word_count = analysis_result.word_count
                analysis.confidence_score = analysis_result.confidence_score
                analysis.processing_time = analysis_result.processing_time
                analysis.visualization_path = analysis_result.visualization_path
                analysis.error_message = analysis_result.error_message
                if hasattr(analysis, "progress_percentage"):
                    analysis.progress_percentage = 100
                if hasattr(analysis, "current_step"):
                    analysis.current_step = "완료"
                db.commit()
        finally:
            db.close()

        # 최종 상태 업데이트
        set_analysis_status(
            analysis_id,
            {
                "progress": 100,
                "step": "완료",
                "status": analysis_result.status,
                "updated_at": datetime.now().isoformat(),
            },
        )

        print(f"✅ 백그라운드 분석 완료: {analysis_id}")

    except Exception as e:
        print(f"❌ 백그라운드 분석 실패: {analysis_id} - {e}")

        # 실패 상태 업데이트
        set_analysis_status(
            analysis_id,
            {
                "progress": 0,
                "step": "분석 실패",
                "status": "failed",
                "error": str(e),
                "updated_at": datetime.now().isoformat(),
            },
        )

        try:
            db = SessionLocal()
            try:
                analysis = (
                    db.query(OCRAnalysis)
                    .filter(OCRAnalysis.analysis_id == analysis_id)
                    .first()
                )
                if analysis:
                    analysis.status = "failed"
                    analysis.error_message = str(e)
                    if hasattr(analysis, "current_step"):
                        analysis.current_step = "분석 실패"
                    db.commit()
            finally:
                db.close()
        except:
            pass

    finally:
        # 임시 파일 정리
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
                print(f"🗑️ 임시 파일 정리: {file_path}")
        except:
            pass


# 비동기 엔드포인트만 유지
@router.post("/ocr/analyze-async", response_model=OCRAsyncResponse)
async def analyze_ocr_async(
    file: UploadFile = File(...),
    engine: str = Form(default="paddle"),
    extract_text_only: bool = Form(default=False),
    visualization: bool = Form(default=True),
    db: Session = Depends(get_db),
):
    """비동기 OCR 분석 시작"""
    if IS_DEBUG:
        print(f"=== 비동기 OCR 분석 요청 ===")
        print(f"파일명: {file.filename}")
        print(f"엔진: {engine}")

    # 파일 형식 검증
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="이미지 파일만 지원됩니다.")

    analysis_id = str(uuid.uuid4())

    try:
        # 임시 파일 저장
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=f"_{file.filename}"
        ) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name

        # DB에 초기 기록 저장
        ocr_analysis = OCRAnalysis(
            analysis_id=analysis_id,
            filename=file.filename or "unknown",
            engine=engine,
            status="queued",
            extracted_text="",
            word_count=0,
            confidence_score=0.0,
            processing_time=0.0,
            extract_text_only=extract_text_only,
            visualization_requested=visualization,
        )
        db.add(ocr_analysis)
        db.commit()

        # 초기 상태 저장
        set_analysis_status(
            analysis_id,
            {
                "progress": 0,
                "step": "대기 중",
                "status": "queued",
                "updated_at": datetime.now().isoformat(),
            },
        )

        # 스레드로 백그라운드 작업 시작 (상태 업데이트 개선)
        thread = threading.Thread(
            target=background_ocr_analysis_thread,
            args=(
                analysis_id,
                temp_file_path,
                file.filename,
                engine,
                extract_text_only,
                visualization,
            ),
        )
        thread.daemon = True
        thread.start()

        estimated_time = "1-2분" if engine == "paddle" else "30-60초"

        return OCRAsyncResponse(
            analysis_id=analysis_id,
            status="queued",
            message="분석이 시작되었습니다. 상태를 확인해주세요.",
            estimated_time=estimated_time,
        )

    except Exception as e:
        print(f"❌ 비동기 OCR 요청 처리 실패: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ocr/status/{analysis_id}", response_model=OCRStatusResponse)
async def get_ocr_status(analysis_id: str, db: Session = Depends(get_db)):
    """OCR 분석 상태 확인"""
    try:
        # 메모리/Redis에서 최신 상태 확인
        status_data = get_analysis_status(analysis_id)

        # DB에서 기본 정보 조회
        analysis = (
            db.query(OCRAnalysis).filter(OCRAnalysis.analysis_id == analysis_id).first()
        )

        if not analysis:
            raise HTTPException(status_code=404, detail="분석 기록을 찾을 수 없습니다.")

        # 상태 정보 조합
        if status_data:
            return OCRStatusResponse(
                analysis_id=analysis_id,
                status=status_data.get("status", analysis.status),
                progress_percentage=status_data.get("progress", 0),
                current_step=status_data.get("step", ""),
                error_message=status_data.get("error", analysis.error_message),
            )

        return OCRStatusResponse(
            analysis_id=analysis_id,
            status=analysis.status,
            progress_percentage=getattr(analysis, "progress_percentage", 0) or 0,
            current_step=getattr(analysis, "current_step", "") or "",
            error_message=analysis.error_message,
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 상태 확인 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ocr/result/{analysis_id}")
async def get_ocr_result(analysis_id: str, db: Session = Depends(get_db)):
    """OCR 분석 결과 조회"""
    try:
        analysis = (
            db.query(OCRAnalysis).filter(OCRAnalysis.analysis_id == analysis_id).first()
        )

        if not analysis:
            raise HTTPException(status_code=404, detail="분석 기록을 찾을 수 없습니다.")

        if analysis.status != "completed":
            raise HTTPException(
                status_code=400, detail="분석이 아직 완료되지 않았습니다."
            )

        # 시각화 이미지 URL 생성
        visualization_url = None
        if analysis.visualization_path and os.path.exists(analysis.visualization_path):
            visualization_url = f"/api/ocr/visualization/{analysis_id}"

        return {
            "analysis_id": analysis_id,
            "filename": analysis.filename,
            "engine": analysis.engine,
            "status": analysis.status,
            "extracted_text": analysis.extracted_text,
            "word_count": analysis.word_count,
            "confidence_score": analysis.confidence_score,
            "processing_time": analysis.processing_time,
            "visualization_url": visualization_url,
            "timestamp": analysis.created_at.isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 결과 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ocr/visualization/{analysis_id}")
async def get_visualization_image(analysis_id: str, db: Session = Depends(get_db)):
    """OCR 시각화 이미지 조회"""
    try:
        analysis = (
            db.query(OCRAnalysis).filter(OCRAnalysis.analysis_id == analysis_id).first()
        )

        if not analysis:
            raise HTTPException(status_code=404, detail="분석 기록을 찾을 수 없습니다.")

        if not analysis.visualization_path or not os.path.exists(
            analysis.visualization_path
        ):
            raise HTTPException(
                status_code=404, detail="시각화 이미지를 찾을 수 없습니다."
            )

        return FileResponse(
            analysis.visualization_path,
            media_type="image/jpeg",
            filename=f"ocr_result_{analysis_id[:8]}.jpg",
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 시각화 이미지 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 기존 호환성 엔드포인트들 유지
@router.get("/ocr/analysis/history/{analysis_id}")
async def get_analysis_history(analysis_id: str, db: Session = Depends(get_db)):
    """OCR 분석 기록 조회 (기존 호환)"""
    try:
        analysis = (
            db.query(OCRAnalysis).filter(OCRAnalysis.analysis_id == analysis_id).first()
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
    db: Session = Depends(get_db),
):
    """OCR 분석 목록 조회 (기존 호환)"""
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
