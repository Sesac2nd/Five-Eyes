import os
import base64
import azure.cognitiveservices.speech as speechsdk
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from models.chat_model import SpeechLog

load_dotenv()


class SpeechService:
    def __init__(self):
        # 주피터 노트북에서 성공한 방식 그대로 사용
        self.speech_key = os.getenv("AZURE_SPEECH_KEY")
        self.service_region = os.getenv("AZURE_SPEECH_REGION")

        print("=== Speech Service 초기화 ===")
        print(f"AZURE_SPEECH_KEY: {'✓' if self.speech_key else '✗'}")
        print(f"AZURE_SPEECH_REGION: {self.service_region}")

        if not self.speech_key or not self.service_region:
            print("⚠️ Azure Speech Service 설정이 누락되었습니다.")
            self.enabled = False
        else:
            self.enabled = True
            print(f"✅ Speech Service 초기화 완료")
            # 주피터에서 성공한 키 확인
            print(f"Key: {self.speech_key[:10]}...")

    def text_to_speech(self, text: str, db: Session = None) -> dict:
        """주피터 노트북에서 성공한 TTS 방식 그대로 적용"""

        log_entry = None
        if db:
            log_entry = SpeechLog(service_type="tts", input_text=text, success=False)

        if not self.enabled:
            error_msg = "Azure Speech Service가 비활성화되었습니다."
            if log_entry:
                log_entry.error_message = error_msg
                db.add(log_entry)
                db.commit()
            return {"success": False, "audio_data": None, "error": error_msg}

        try:
            print(f"🎵 TTS 시작: {text[:50]}...")

            # 주피터 노트북과 동일한 방식
            speech_config = speechsdk.SpeechConfig(
                subscription=self.speech_key, region=self.service_region
            )

            # 한국어 음성으로 변경 (주피터에서는 영어였지만 한국어로)
            speech_config.speech_synthesis_voice_name = "ko-KR-SunHiNeural"

            # 주피터와 동일: 기본 스피커 사용하지 않고 메모리로
            speech_synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=speech_config, audio_config=None  # 메모리로 받기
            )

            print("🔄 음성 합성 중...")
            # 주피터와 동일한 방식
            result = speech_synthesizer.speak_text_async(text).get()

            print(f"📊 결과: {result.reason}")

            # 주피터와 동일한 체크 로직
            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                print("✅ Speech synthesized successfully")

                # 오디오 데이터 가져오기
                audio_data = result.audio_data
                audio_length = len(audio_data)
                print(f"📦 오디오 크기: {audio_length} bytes")

                # Base64 인코딩
                audio_base64 = base64.b64encode(audio_data).decode("utf-8")
                print(f"✅ Base64 인코딩 완료")

                # 로그 저장
                if log_entry:
                    log_entry.success = True
                    log_entry.audio_length = audio_length
                    db.add(log_entry)
                    db.commit()

                return {"success": True, "audio_data": audio_base64, "error": None}

            elif result.reason == speechsdk.ResultReason.Canceled:
                # 주피터와 동일한 에러 처리
                cancellation_details = result.cancellation_details
                error_msg = f"Speech synthesis canceled: {cancellation_details.reason}"

                if cancellation_details.reason == speechsdk.CancellationReason.Error:
                    error_details = cancellation_details.error_details
                    error_msg += f" - Error details: {error_details}"
                    print(f"❌ Error details: {error_details}")

                print(f"❌ {error_msg}")

                # 로그 저장
                if log_entry:
                    log_entry.error_message = error_msg
                    db.add(log_entry)
                    db.commit()

                return {"success": False, "audio_data": None, "error": error_msg}
            else:
                error_msg = f"Unexpected result: {result.reason}"
                print(f"❌ {error_msg}")

                if log_entry:
                    log_entry.error_message = error_msg
                    db.add(log_entry)
                    db.commit()

                return {"success": False, "audio_data": None, "error": error_msg}

        except Exception as e:
            error_msg = f"TTS Exception: {str(e)}"
            print(f"❌ {error_msg}")

            if log_entry:
                log_entry.error_message = error_msg
                db.add(log_entry)
                db.commit()

            return {"success": False, "audio_data": None, "error": error_msg}

    def speech_to_text(self, audio_data: bytes, db: Session = None) -> dict:
        """STT 서비스 (나중에 구현)"""

        log_entry = None
        if db:
            log_entry = SpeechLog(
                service_type="stt", success=False, audio_length=len(audio_data)
            )

        if not self.enabled:
            error_msg = "Azure Speech Service가 비활성화되었습니다."
            if log_entry:
                log_entry.error_message = error_msg
                db.add(log_entry)
                db.commit()
            return {"success": False, "text": "", "error": error_msg}

        try:
            print(f"🎤 STT 시작: {len(audio_data)} bytes")

            # STT 설정
            speech_config = speechsdk.SpeechConfig(
                subscription=self.speech_key, region=self.service_region
            )
            speech_config.speech_recognition_language = "ko-KR"

            # 오디오 스트림 설정
            audio_stream = speechsdk.audio.PushAudioInputStream()
            audio_config = speechsdk.audio.AudioConfig(stream=audio_stream)
            speech_recognizer = speechsdk.SpeechRecognizer(
                speech_config=speech_config, audio_config=audio_config
            )

            # 오디오 데이터 푸시
            audio_stream.write(audio_data)
            audio_stream.close()

            # 음성 인식
            result = speech_recognizer.recognize_once_async().get()

            if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                recognized_text = result.text
                print(f"✅ STT 성공: {recognized_text}")

                if log_entry:
                    log_entry.success = True
                    log_entry.input_text = recognized_text
                    db.add(log_entry)
                    db.commit()

                return {"success": True, "text": recognized_text, "error": None}
            else:
                error_msg = f"STT failed: {result.reason}"
                print(f"❌ {error_msg}")

                if log_entry:
                    log_entry.error_message = error_msg
                    db.add(log_entry)
                    db.commit()

                return {"success": False, "text": "", "error": error_msg}

        except Exception as e:
            error_msg = f"STT Exception: {str(e)}"
            print(f"❌ {error_msg}")

            if log_entry:
                log_entry.error_message = error_msg
                db.add(log_entry)
                db.commit()

            return {"success": False, "text": "", "error": error_msg}


# 전역 인스턴스
speech_service = SpeechService()
