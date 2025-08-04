import { useRef } from "react";
import axios from "axios";

/**
 * useVoiceSpeaker 훅
 * - speak(text): Promise (음성 출력이 완료되면 resolve)
 * - 서버 TTS(/api/tts, Azure 활용)에 먼저 요청, 실패 시 브라우저 기본 합성 사용
 * - 여러 개의 음성 요청도 안전하게 큐잉하여 순차 재생
 */
export default function useVoiceSpeaker() {
  const audioQueueRef = useRef([]);
  const isSpeakingRef = useRef(false);

  // 사용자 함수: speak(text)
  const speak = (text) => {
    return new Promise((resolve) => {
      audioQueueRef.current.push({ text, resolve });
      if (!isSpeakingRef.current) processAudioQueue();
    });
  };

  // 내부적으로 큐를 순차 실행
  const processAudioQueue = async () => {
    if (isSpeakingRef.current || audioQueueRef.current.length === 0) return;
    isSpeakingRef.current = true;
    const { text, resolve } = audioQueueRef.current.shift();

    try {
      // 1. Azure TTS (서버 API) 호출
      const response = await axios.post("/api/tts", `text=${encodeURIComponent(text.trim())}`, {
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        timeout: 15000,
      });

      const audioData = response.data.audio_data; // base64 string
      const audioBlob = new Blob([Uint8Array.from(atob(audioData), (c) => c.charCodeAt(0))], {
        type: "audio/wav",
      });
      const audio = new Audio(URL.createObjectURL(audioBlob));
      audio.onended = () => {
        isSpeakingRef.current = false;
        processAudioQueue();
        resolve();
      };
      audio.play();
    } catch (error) {
      // 2. Fallback: 브라우저 SpeechSynthesis
      const utterance = new window.SpeechSynthesisUtterance(text);
      utterance.lang = "ko-KR";
      utterance.rate = 1.0;
      utterance.onend = () => {
        isSpeakingRef.current = false;
        processAudioQueue();
        resolve();
      };
      window.speechSynthesis.speak(utterance);
    }
  };

  return { speak };
}
