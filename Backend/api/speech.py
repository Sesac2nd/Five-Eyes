from fastapi import APIRouter, HTTPException, Form, File, UploadFile, Depends
from sqlalchemy.orm import Session
from services.speech_service import speech_service
from config.database import get_db

router = APIRouter()


@router.post("/tts")
async def text_to_speech(text: str = Form(...), db: Session = Depends(get_db)):
    """
    텍스트를 음성으로 변환 (주피터 노트북 방식 기반)
    """
    print(f"=== TTS API 요청 ===")
    print(f"텍스트: {text}")

    if not text or not text.strip():
        raise HTTPException(status_code=400, detail="Text is required")

    try:
        result = speech_service.text_to_speech(text.strip(), db)

        if result["success"]:
            print(f"✅ TTS API 성공")
            return {"audio_data": result["audio_data"]}
        else:
            print(f"❌ TTS API 실패: {result['error']}")
            raise HTTPException(status_code=500, detail=result["error"])

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ TTS API 예외: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stt")
async def speech_to_text(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    음성을 텍스트로 변환
    """
    print(f"=== STT API 요청 ===")
    print(f"파일: {file.filename}")

    try:
        audio_data = await file.read()
        result = speech_service.speech_to_text(audio_data, db)

        if result["success"]:
            print(f"✅ STT API 성공: {result['text']}")
            return {"text": result["text"]}
        else:
            print(f"❌ STT API 실패: {result['error']}")
            raise HTTPException(status_code=500, detail=result["error"])

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ STT API 예외: {e}")
        raise HTTPException(status_code=500, detail=str(e))
