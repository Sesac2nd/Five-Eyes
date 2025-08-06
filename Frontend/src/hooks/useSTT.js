import { useState, useRef, useCallback } from "react";
import axios from "axios";

/**
 * useSTT 훅
 * - startRecording(): 녹음 시작
 * - stopRecording(): 녹음 중지 및 텍스트 변환
 * - isRecording: 녹음 상태
 * - transcript: 변환된 텍스트
 * - error: 에러 메시지
 */
export default function useSTT() {
  const [isRecording, setIsRecording] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [error, setError] = useState(null);

  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  const startRecording = useCallback(async () => {
    try {
      setError(null);
      setTranscript("");

      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: "audio/wav" });
        await sendAudioToServer(audioBlob);

        // 스트림 정리
        stream.getTracks().forEach((track) => track.stop());
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (err) {
      setError("마이크 접근 권한이 필요합니다.");
      console.error("Microphone access error:", err);
    }
  }, []);

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  }, [isRecording]);

  const sendAudioToServer = async (audioBlob) => {
    try {
      const formData = new FormData();
      formData.append("file", audioBlob, "recording.wav");

      const response = await axios.post("/api/stt/upload", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
        timeout: 30000,
      });

      setTranscript(response.data.text);
    } catch (err) {
      setError("음성 변환에 실패했습니다.");
      console.error("STT error:", err);

      // Fallback: 브라우저 Web Speech API 사용
      fallbackToWebSpeechAPI();
    }
  };

  const fallbackToWebSpeechAPI = () => {
    if (!("webkitSpeechRecognition" in window) && !("SpeechRecognition" in window)) {
      setError("브라우저에서 음성 인식을 지원하지 않습니다.");
      return;
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();

    recognition.lang = "ko-KR";
    recognition.continuous = false;
    recognition.interimResults = false;

    recognition.onresult = (event) => {
      const result = event.results[0][0].transcript;
      setTranscript(result);
    };

    recognition.onerror = (event) => {
      setError(`음성 인식 오류: ${event.error}`);
    };

    recognition.start();
  };

  return {
    startRecording,
    stopRecording,
    isRecording,
    transcript,
    error,
  };
}
