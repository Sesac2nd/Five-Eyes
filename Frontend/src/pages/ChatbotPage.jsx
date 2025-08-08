import { useState, useRef, useEffect } from "react";
import { Send, Mic, MicOff, Volume2, Copy, RotateCcw } from "lucide-react";
import useTTS from "@/hooks/useTTS";
import useSTT from "@/hooks/useSTT";
import "@/styles/pages/ChatbotPage.css";

function ChatbotPage() {
  const [messages, setMessages] = useState([
    {
      id: 1,
      type: "bot",
      content: "안녕하세요! 저는 조선왕조실록 기반 역사 AI입니다. 조선시대에 대한 궁금한 점을 물어보세요.",
      timestamp: new Date(),
      keywords: ["조선왕조실록", "역사", "AI"],
    },
  ]);
  const [inputMessage, setInputMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [chatMode, setChatMode] = useState("verification"); // verification | creative
  const [showSuggestions, setShowSuggestions] = useState(true);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [toastMessage, setToastMessage] = useState("");
  const [toastType, setToastType] = useState("success");
  const toastTimeoutRef = useRef(null);

  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // TTS/STT 훅 사용
  const { speak } = useTTS();
  const { startRecording, stopRecording, isRecording, transcript, error: sttError } = useSTT();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const prevMessagesRef = useRef([]);
  const isInitialLoadRef = useRef(true); // 초기 로드 여부 판단용

  useEffect(() => {
    if (isInitialLoadRef.current) {
      // messages 길이가 더 길어졌을 때만(새 메시지 추가) 자동 스크롤
      isInitialLoadRef.current = false;
    } else {
      // 이후 새 메시지 추가 시에만 스크롤 이동
      if (prevMessagesRef.current.length < messages.length) {
        scrollToBottom();
      }
    }
    prevMessagesRef.current = messages;
  }, [messages]);


  // STT 결과가 있을 때 input에 반영
  useEffect(() => {
    if (transcript) {
      setInputMessage(transcript);
      inputRef.current?.focus();
      showToast("음성이 텍스트로 변환되었습니다!");
    }
  }, [transcript]);

  // STT 에러 처리
  useEffect(() => {
    if (sttError) {
      showToast(`음성 인식 오류: ${sttError}`, "error");
    }
  }, [sttError]);

  // ESC 키로 TTS 중단 처리 추가
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === "Escape" && isSpeaking) {
        // TTS 중단
        if (window.speechSynthesis) {
          window.speechSynthesis.cancel();
        }
        // 상태 초기화 (이 때 useEffect가 트리거되어 완료 토스트가 표시될 수 있음)
        setIsSpeaking(false);
        // 별도의 중단 토스트 표시 (기존 토스트를 덮어씀)
        setTimeout(() => {
          showToast("🛑 음성 출력이 중단되었습니다.", "warning", 2000); // 2초 후 제거
        }, 100); // 약간의 지연을 두어 상태 변화 useEffect 이후에 실행
        console.log("🛑 ESC로 TTS 중단 및 상태 초기화");
      }
    };

    // 전역 키보드 이벤트 리스너 등록
    document.addEventListener("keydown", handleKeyDown);

    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      // 컴포넌트 언마운트 시 타이머 정리
      if (toastTimeoutRef.current) {
        clearTimeout(toastTimeoutRef.current);
      }
    };
  }, [isSpeaking]); // isSpeaking 의존성 추가

  // TTS 상태 변화 감지 및 토스트 표시
  useEffect(() => {
    if (isSpeaking) {
      showToast("🎵 음성 출력 중... (ESC 키로 중단 가능)", "info", 0); // 지속적 표시
    } else {
      // TTS가 중단되거나 완료되면 2초 후 토스트 숨김 (단, 다른 메시지가 있으면 유지)
      if (toastMessage.includes("음성 출력 중")) {
        showToast("🎵 음성 출력이 완료되었습니다.", "success", 2000); // 2초 후 자동 제거
      }
    }
  }, [isSpeaking]);

  // STT 상태 변화 감지 및 토스트 표시
  useEffect(() => {
    if (isRecording) {
      showToast("🎤 음성을 인식하고 있습니다... (다시 클릭하여 중지)", "info", 0); // 지속적 표시
    } else {
      // STT가 중단되면 2초 후 토스트 숨김 (단, 다른 메시지가 있으면 유지)
      if (toastMessage.includes("음성을 인식하고")) {
        showToast("🎤 음성 인식이 완료되었습니다.", "success", 2000); // 2초 후 자동 제거
      }
    }
  }, [isRecording]);

  const showToast = (message, type = "success", duration = 3000) => {
    // 기존 타이머 클리어
    if (toastTimeoutRef.current) {
      clearTimeout(toastTimeoutRef.current);
    }

    setToastMessage(message);
    setToastType(type);

    // 지속적 표시가 필요한 경우 (duration이 0이면 수동으로 닫아야 함)
    if (duration > 0) {
      toastTimeoutRef.current = setTimeout(() => {
        setToastMessage("");
        setToastType("success");
      }, duration);
    }
  };

  const hideToast = () => {
    if (toastTimeoutRef.current) {
      clearTimeout(toastTimeoutRef.current);
    }
    setToastMessage("");
    setToastType("success");
  };

    // // 호출하는 곳에서 사용법 (async/await 처리 필요)
  const handleSendMessage = async () => {
    if (!inputMessage.trim()) return;

    // 사용자 메시지 추가
    const userMessage = {
      id: Date.now(),
      type: "user",
      content: inputMessage,
      timestamp: new Date(),
    };
    
    setMessages(prev => [...prev, userMessage]);
    const query = inputMessage;
    setInputMessage("");

    try {
      // 로딩 상태 표시
      setIsLoading(true);
      
      // API 호출 (await 사용)
      const botResponse = await generateBotResponse(query, chatMode);
      
      // 봇 응답 추가
      setMessages(prev => [...prev, botResponse]);
      
    } catch (error) {
      console.error('메시지 전송 오류:', error);
      
      // 에러 메시지 표시
      const errorMessage = {
        id: Date.now() + 1,
        type: "bot",
        content: "죄송합니다. 메시지 처리 중 오류가 발생했습니다.",
        timestamp: new Date(),
        error: true
      };
      
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  // 기존 목업 함수를 API 호출로 변경
  const generateBotResponse = async (query, chatMode = "verification") => {
    try {
      // API 요청 데이터 구성
      const requestData = {
        session_id: `session_${Date.now()}`, // 또는 실제 세션 ID 사용
        message_type: "user",
        message: query,
        audio_requested: false,
        is_verify: chatMode === 'verification', // true면 고증, false면 창작
        top_n_documents: 5,
        strictness: 2
      };

      console.log('API 요청 데이터:', requestData);

      // API 호출
      const response = await fetch('http://localhost:8001/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData)
      });

      // 응답 처리
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log('API 응답 데이터:', data);

      // API 응답을 프론트엔드 형식으로 변환
      return {
        id: Date.now() + 1,
        type: "bot",
        content: data.response || "응답을 받지 못했습니다.",
        timestamp: new Date(data.timestamp || Date.now()),
        keywords: data.keywords || [],
        sources: data.sources || [],
        // API에서 추가 데이터가 있다면 여기에 매핑
        session_id: data.session_id,
        apiResponse: data // 디버깅용으로 전체 응답 보관
      };

    } catch (error) {
      console.error('API 호출 오류:', error);
    }
  };

  const handleKeywordClick = (keyword) => {
    setInputMessage(keyword + "에 대해 더 자세히 알려주세요");
    inputRef.current?.focus();
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  // TTS 기능 구현 - 개선된 버전
  const handleSpeakMessage = async (content) => {
    if (isSpeaking) {
      showToast("이미 음성 출력 중입니다.", "warning");
      return;
    }

    try {
      setIsSpeaking(true);

      // 마크다운 형식 및 특수 문자 제거
      const cleanContent = content
        .replace(/\*\*/g, "") // ** 제거
        .replace(/📚|✨|🎯/g, "") // 이모지 제거
        .replace(/\n+/g, " ") // 개행 문자를 공백으로
        .replace(/\s+/g, " ") // 연속 공백 정리
        .trim();

      console.log("🎵 TTS 시작:", cleanContent.substring(0, 50) + "...");

      // useTTS 훅의 speak 함수 호출
      await speak(cleanContent);

      console.log("🎵 TTS 완료");
      // TTS 정상 완료 시에는 토스트를 바로 완료 메시지로 변경하지 않음
      // useEffect에서 isSpeaking 상태 변화를 감지하여 처리함
    } catch (error) {
      console.error("TTS 오류:", error);
      showToast("음성 출력에 실패했습니다.", "error");
    } finally {
      // TTS 완료 또는 오류 시 상태 초기화
      setIsSpeaking(false);
      console.log("🔄 TTS 상태 초기화 완료");
    }
  };

  // STT 기능 구현 - 실제 음성 인식
  const toggleListening = async () => {
    if (isRecording) {
      try {
        await stopRecording();
        // STT 중지 토스트는 useEffect에서 처리됨
      } catch (error) {
        console.error("STT 중지 오류:", error);
        showToast("음성 인식 중지에 실패했습니다.", "error");
      }
    } else {
      try {
        await startRecording();
        // STT 시작 토스트는 useEffect에서 처리됨
      } catch (error) {
        console.error("STT 시작 오류:", error);
        showToast("마이크 접근 권한이 필요합니다.", "error");
      }
    }
  };

  const handleCopyMessage = async (content) => {
    try {
      await navigator.clipboard.writeText(content);
      showToast("클립보드에 복사되었습니다!");
    } catch (error) {
      console.error("복사 오류:", error);
      showToast("복사에 실패했습니다.", "error");
    }
  };

  const handleReset = () => {
    setMessages([
      {
        id: 1,
        type: "bot",
        content: "대화가 초기화되었습니다. 새로운 질문을 해주세요!",
        timestamp: new Date(),
        keywords: [],
      },
    ]);
    showToast("대화가 초기화되었습니다.");
    setShowSuggestions(true);  // 리셋 시 추천 질문 다시 보이도록 설정
  };

  const suggestedQuestions = ["세종대왕이 가장 좋아한 음식은 무엇인가요?", "조선시대 궁중의 하루 일과는 어떠했나요?", "임진왜란 당시 의병 활동은 어떠했나요?", "영조의 균역법 개혁 배경을 알려주세요", "정조의 수원화성 건설 이유는 무엇인가요?"];

  return (
    <div className={`chatbot-page ${chatMode}`}>
      {/* 토스트 메시지 */}
      {toastMessage && (
        <div className={`toast-message ${toastType}`}>
          {toastMessage}
          {/* 지속적 토스트의 경우에만 닫기 버튼 제공 */}
          {(toastMessage.includes("음성 출력 중") || toastMessage.includes("음성을 인식하고")) && (
            <button className="toast-close-btn" onClick={hideToast} title="닫기">
              ×
            </button>
          )}
        </div>
      )}

      <div className="chat-header">
        <div className="chat-title">
          <h1>역사 AI 챗봇</h1>
          <p>조선왕조실록 기반 질의응답 및 창작 지원</p>
        </div>

        <div className="chat-modes">
          <button className={`mode-btn ${chatMode === "verification" ? "active verification" : ""}`} onClick={() => setChatMode("verification")}>
            📚 고증 검증
          </button>
          <button className={`mode-btn ${chatMode === "creative" ? "active creative" : ""}`} onClick={() => setChatMode("creative")}>
            ✨ 창작 도우미
          </button>
        </div>
      </div>

      <div className="chat-container">
        <div className="messages-container">
          {messages.map((message) => (
            <div key={message.id} className={`message ${message.type}`}>
              <div className="message-content">
                <div className="message-text">
                  {message.content.split("\n").map((line, index) => (
                    <p key={index}>{line}</p>
                  ))}
                </div>

                {message.keywords && message.keywords.length > 0 && (
                  <div className="message-keywords">
                    {message.keywords.map((keyword, index) => (
                      <button key={index} className="keyword-btn" onClick={() => handleKeywordClick(keyword)}>
                        {keyword}
                      </button>
                    ))}
                  </div>
                )}

                {message.sources && (
                  <div className="message-sources">
                    <strong>출처:</strong> {message.sources.join(", ")}
                  </div>
                )}
              </div>

              {message.type === "bot" && (
                <div className="message-actions">
                  <button className={`action-btn ${isSpeaking ? "speaking" : ""}`} onClick={() => handleSpeakMessage(message.content)} title={isSpeaking ? "음성 출력 중... (ESC로 중단)" : "음성으로 듣기"} disabled={false}>
                    <Volume2 size={16} />
                  </button>
                  <button className="action-btn" onClick={() => handleCopyMessage(message.content)} title="복사하기">
                    <Copy size={16} />
                  </button>
                </div>
              )}

              <div className="message-time">{message.timestamp.toLocaleTimeString()}</div>
            </div>
          ))}

          {isLoading && (
            <div className="message bot loading">
              <div className="message-content">
                <div className="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {showSuggestions && (
          <div className="suggested-questions">
            <h3>추천 질문</h3>
            <div className="questions-list">
              {suggestedQuestions.map((question, index) => (
                <button 
                  key={index} 
                  className="suggestion-btn" 
                  onClick={ () => {
                    setInputMessage(question);
                    setShowSuggestions(false); 
                  }}
                >
                  {question}
                </button>
              ))}
            </div>
          </div>
        )}

        <div className="chat-input-container">
          <div className="input-actions">
            <button className="action-btn" onClick={handleReset} title="대화 초기화">
              <RotateCcw size={18} />
            </button>
            <button className={`action-btn ${isRecording ? "recording" : ""}`} onClick={toggleListening} title={isRecording ? "음성 입력 중지" : "음성 입력 시작"} disabled={isLoading}>
              {isRecording ? <MicOff size={18} /> : <Mic size={18} />}
            </button>
          </div>

          <div className="input-wrapper">
            <textarea ref={inputRef} value={inputMessage} onChange={(e) => setInputMessage(e.target.value)} onKeyPress={handleKeyPress} placeholder={`${chatMode === "verification" ? "역사적 사실에 대해 질문해보세요..." : "창작하고 싶은 내용을 말씀해주세요..."}`} rows="1" className="chat-input" disabled={isRecording} />
            <button className="send-btn" onClick={handleSendMessage} disabled={!inputMessage.trim() || isLoading || isRecording}>
              <Send size={18} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default ChatbotPage;
