import { useRef, useEffect } from "react";
import axios from "axios";

export default function useTTS() {
  const audioQueueRef = useRef([]);
  const isSpeakingRef = useRef(false);
  const currentAudioRef = useRef(null);

  const speak = (text) => {
    return new Promise((resolve) => {
      audioQueueRef.current.push({ text, resolve });
      if (!isSpeakingRef.current) processAudioQueue();
    });
  };

  const stopSpeaking = () => {
    if (currentAudioRef.current) {
      currentAudioRef.current.pause();
      currentAudioRef.current = null;
    }

    if ("speechSynthesis" in window) {
      window.speechSynthesis.cancel();
    }

    audioQueueRef.current = [];
    isSpeakingRef.current = false;

    console.log("🛑 TTS 중지됨");
  };

  const processAudioQueue = async () => {
    if (isSpeakingRef.current || audioQueueRef.current.length === 0) return;
    isSpeakingRef.current = true;
    const { text, resolve } = audioQueueRef.current.shift();

    try {
      const response = await axios.post("/api/tts", `text=${encodeURIComponent(text.trim())}`, {
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        timeout: 15000,
      });

      const audioData = response.data.audio_data;
      const audioBlob = new Blob([Uint8Array.from(atob(audioData), (c) => c.charCodeAt(0))], {
        type: "audio/wav",
      });
      const audio = new Audio(URL.createObjectURL(audioBlob));
      currentAudioRef.current = audio;

      audio.onended = () => {
        currentAudioRef.current = null;
        isSpeakingRef.current = false;
        processAudioQueue();
        resolve();
      };

      audio.onerror = () => {
        currentAudioRef.current = null;
        fallbackToSpeechSynthesis(text, resolve);
      };

      audio.play();
    } catch (error) {
      fallbackToSpeechSynthesis(text, resolve);
    }
  };

  const fallbackToSpeechSynthesis = (text, resolve) => {
    const utterance = new window.SpeechSynthesisUtterance(text);
    utterance.lang = "ko-KR";
    utterance.rate = 1.0;
    utterance.onend = () => {
      isSpeakingRef.current = false;
      processAudioQueue();
      resolve();
    };
    utterance.onerror = () => {
      isSpeakingRef.current = false;
      processAudioQueue();
      resolve();
    };
    window.speechSynthesis.speak(utterance);
  };

  // ✅ Esc 키 입력으로 stopSpeaking() 호출
  useEffect(() => {
    const handleKeyDown = (event) => {
      if (event.key === "Escape") {
        stopSpeaking();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, []);

  return { speak, stopSpeaking };
}
