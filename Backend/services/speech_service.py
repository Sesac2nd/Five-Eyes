import os
import io
import base64
import tempfile
import logging
from typing import Dict, Optional, List
from config.settings import settings

logger = logging.getLogger(__name__)


class SpeechService:
    """Azure Speech Service를 이용한 STT/TTS 서비스"""

    def __init__(self):
        self.enabled = False
        self.speech_key = settings.AZURE_SPEECH_KEY
        self.speech_region = settings.AZURE_SPEECH_REGION
        self._initialize_service()

    def _initialize_service(self):
        """Azure Speech Service 초기화"""
        try:
            if not self.speech_key or self.speech_key == "":
                logger.error("❌ Azure Speech Service 키가 설정되지 않았습니다.")
                return

            if not self.speech_region or self.speech_region == "":
                logger.error("❌ Azure Speech Service 리전이 설정되지 않았습니다.")
                return

            # Azure Speech SDK import 확인
            import azure.cognitiveservices.speech as speechsdk

            # 기본 설정 테스트
            speech_config = speechsdk.SpeechConfig(
                subscription=self.speech_key, region=self.speech_region
            )

            self.enabled = True
            logger.info("✅ Azure Speech Service 초기화 성공")

        except ImportError:
            logger.error("❌ Azure Speech SDK가 설치되지 않았습니다.")
            logger.info("💡 설치 방법: pip install azure-cognitiveservices-speech")
        except Exception as e:
            logger.error(f"❌ Azure Speech Service 초기화 실패: {e}")

    def text_to_speech(
        self,
        text: str,
        voice_name: str = "ko-KR-HyunsuMultilingualNeural",
        output_format: str = "wav",
    ) -> Dict:
        """텍스트를 음성으로 변환"""
        if not self.enabled:
            return {
                "success": False,
                "error": "Azure Speech Service가 비활성화되어 있습니다.",
                "audio_data": None,
            }

        try:
            import azure.cognitiveservices.speech as speechsdk

            # Speech 설정
            speech_config = speechsdk.SpeechConfig(
                subscription=self.speech_key, region=self.speech_region
            )
            speech_config.speech_synthesis_voice_name = voice_name

            # 오디오 출력 설정 (메모리 스트림)
            audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=False)
            speech_synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=speech_config, audio_config=audio_config
            )

            # 음성 합성 실행
            logger.info(f"🔊 TTS 요청: '{text[:50]}...' (음성: {voice_name})")
            result = speech_synthesizer.speak_text_async(text).get()

            # 결과 확인
            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                # Base64로 인코딩
                audio_base64 = base64.b64encode(result.audio_data).decode("utf-8")

                logger.info(f"✅ TTS 성공: {len(result.audio_data)} bytes")

                return {
                    "success": True,
                    "audio_data": audio_base64,
                    "audio_size": len(result.audio_data),
                    "voice_name": voice_name,
                    "text": text,
                    "format": output_format,
                }

            elif result.reason == speechsdk.ResultReason.Canceled:
                cancellation_details = result.cancellation_details
                error_msg = f"TTS 취소됨: {cancellation_details.reason}"

                if cancellation_details.reason == speechsdk.CancellationReason.Error:
                    error_msg += f" - {cancellation_details.error_details}"

                logger.error(f"❌ {error_msg}")
                return {"success": False, "error": error_msg, "audio_data": None}
            else:
                return {
                    "success": False,
                    "error": "음성 합성에 실패했습니다.",
                    "audio_data": None,
                }

        except Exception as e:
            logger.error(f"❌ TTS 오류: {e}")
            return {
                "success": False,
                "error": f"음성 합성 오류: {str(e)}",
                "audio_data": None,
            }

    def speech_to_text(
        self, audio_data: bytes, language: str = "ko-KR", audio_format: str = "wav"
    ) -> Dict:
        """음성을 텍스트로 변환"""
        if not self.enabled:
            return {
                "success": False,
                "error": "Azure Speech Service가 비활성화되어 있습니다.",
                "recognized_text": "",
            }

        try:
            import azure.cognitiveservices.speech as speechsdk

            # Speech 설정
            speech_config = speechsdk.SpeechConfig(
                subscription=self.speech_key, region=self.speech_region
            )
            speech_config.speech_recognition_language = language

            # 침묵 감지 시간 설정 (8초)
            speech_config.set_property(
                speechsdk.PropertyId.SpeechServiceConnection_EndSilenceTimeoutMs, "8000"
            )

            # 임시 파일로 오디오 저장
            with tempfile.NamedTemporaryFile(
                suffix=f".{audio_format}", delete=False
            ) as temp_file:
                temp_file.write(audio_data)
                temp_file_path = temp_file.name

            try:
                # 파일 기반 오디오 설정
                audio_config = speechsdk.audio.AudioConfig(filename=temp_file_path)
                speech_recognizer = speechsdk.SpeechRecognizer(
                    speech_config=speech_config, audio_config=audio_config
                )

                logger.info(f"🎤 STT 요청: {len(audio_data)} bytes ({language})")

                # 음성 인식 실행
                result = speech_recognizer.recognize_once_async().get()

                if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                    recognized_text = result.text.strip()
                    logger.info(f"✅ STT 성공: '{recognized_text}'")

                    return {
                        "success": True,
                        "recognized_text": recognized_text,
                        "confidence": 0.85,  # Azure는 신뢰도를 직접 제공하지 않음
                        "language": language,
                        "audio_duration": len(audio_data) / 16000,  # 대략적인 추정
                    }

                elif result.reason == speechsdk.ResultReason.NoMatch:
                    logger.warning("⚠️ STT: 음성 매칭 없음")
                    return {
                        "success": False,
                        "error": "음성을 인식할 수 없습니다. 더 명확하게 말씀해 주세요.",
                        "recognized_text": "",
                    }

                elif result.reason == speechsdk.ResultReason.Canceled:
                    cancellation_details = result.cancellation_details
                    error_msg = f"STT 취소됨: {cancellation_details.reason}"

                    if (
                        cancellation_details.reason
                        == speechsdk.CancellationReason.Error
                    ):
                        error_msg += f" - {cancellation_details.error_details}"

                    logger.error(f"❌ {error_msg}")
                    return {"success": False, "error": error_msg, "recognized_text": ""}
                else:
                    return {
                        "success": False,
                        "error": "음성 인식에 실패했습니다.",
                        "recognized_text": "",
                    }

            finally:
                # 임시 파일 정리
                try:
                    os.remove(temp_file_path)
                except:
                    pass

        except Exception as e:
            logger.error(f"❌ STT 오류: {e}")
            return {
                "success": False,
                "error": f"음성 인식 오류: {str(e)}",
                "recognized_text": "",
            }

    def get_available_voices(self, language: str = "ko-KR") -> Dict:
        """사용 가능한 음성 목록 조회"""
        korean_voices = [
            {
                "name": "ko-KR-HyunsuMultilingualNeural",
                "gender": "Male",
                "description": "한국어 남성 음성 (다국어 지원)",
                "recommended": True,
            },
            {
                "name": "ko-KR-SunHiNeural",
                "gender": "Female",
                "description": "한국어 여성 음성",
                "recommended": True,
            },
            {
                "name": "ko-KR-InJoonNeural",
                "gender": "Male",
                "description": "한국어 남성 음성",
            },
            {
                "name": "ko-KR-BongJinNeural",
                "gender": "Male",
                "description": "한국어 남성 음성",
            },
            {
                "name": "ko-KR-GookMinNeural",
                "gender": "Male",
                "description": "한국어 남성 음성",
            },
        ]

        chinese_voices = [
            {
                "name": "zh-CN-XiaoxiaoNeural",
                "gender": "Female",
                "description": "중국어 간체 여성 음성",
            },
            {
                "name": "zh-CN-YunxiNeural",
                "gender": "Male",
                "description": "중국어 간체 남성 음성",
            },
            {
                "name": "zh-TW-HsiaoChenNeural",
                "gender": "Female",
                "description": "중국어 번체 여성 음성",
            },
        ]

        if language.startswith("ko"):
            return {
                "language": language,
                "voices": korean_voices,
                "default": "ko-KR-HyunsuMultilingualNeural",
            }
        elif language.startswith("zh"):
            return {
                "language": language,
                "voices": chinese_voices,
                "default": "zh-CN-XiaoxiaoNeural",
            }
        else:
            return {
                "language": language,
                "voices": korean_voices + chinese_voices,
                "default": "ko-KR-HyunsuMultilingualNeural",
            }

    def create_ssml(
        self, text: str, voice_name: str, rate: str = "medium", pitch: str = "medium"
    ) -> str:
        """SSML 형식으로 텍스트 변환"""
        ssml = f"""
        <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="ko-KR">
            <voice name="{voice_name}">
                <prosody rate="{rate}" pitch="{pitch}">
                    {text}
                </prosody>
            </voice>
        </speak>
        """
        return ssml.strip()

    def text_to_speech_with_ssml(self, ssml: str) -> Dict:
        """SSML을 사용한 고급 음성 합성"""
        if not self.enabled:
            return {
                "success": False,
                "error": "Azure Speech Service가 비활성화되어 있습니다.",
                "audio_data": None,
            }

        try:
            import azure.cognitiveservices.speech as speechsdk

            # Speech 설정
            speech_config = speechsdk.SpeechConfig(
                subscription=self.speech_key, region=self.speech_region
            )

            # 오디오 출력 설정
            audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=False)
            speech_synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=speech_config, audio_config=audio_config
            )

            # SSML로 음성 합성
            result = speech_synthesizer.speak_ssml_async(ssml).get()

            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                audio_base64 = base64.b64encode(result.audio_data).decode("utf-8")

                return {
                    "success": True,
                    "audio_data": audio_base64,
                    "audio_size": len(result.audio_data),
                    "ssml": ssml,
                }
            else:
                return {
                    "success": False,
                    "error": "SSML 음성 합성 실패",
                    "audio_data": None,
                }

        except Exception as e:
            logger.error(f"❌ SSML TTS 오류: {e}")
            return {
                "success": False,
                "error": f"SSML 음성 합성 오류: {str(e)}",
                "audio_data": None,
            }

    def get_service_info(self) -> Dict:
        """서비스 정보 반환"""
        return {
            "service_name": "Azure Speech Service",
            "enabled": self.enabled,
            "region": self.speech_region if self.enabled else "Not configured",
            "features": [
                "텍스트 음성 변환 (TTS)",
                "음성 텍스트 변환 (STT)",
                "다국어 지원",
                "SSML 지원",
                "실시간 음성 인식",
            ],
            "supported_languages": [
                "ko-KR (한국어)",
                "zh-CN (중국어 간체)",
                "zh-TW (중국어 번체)",
                "ja-JP (일본어)",
                "en-US (영어)",
            ],
            "audio_formats": ["WAV", "MP3", "OGG"],
        }


# 전역 서비스 인스턴스
speech_service = SpeechService()
