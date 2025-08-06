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
      content:
        "안녕하세요! 저는 조선왕조실록 기반 역사 AI입니다. 조선시대에 대한 궁금한 점을 물어보세요.",
      timestamp: new Date(),
      keywords: ["조선왕조실록", "역사", "AI"],
    },
  ]);
  const [inputMessage, setInputMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [chatMode, setChatMode] = useState("verification"); // verification | creative
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [toastMessage, setToastMessage] = useState("");

  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // TTS/STT 훅 사용
  const { speak } = useTTS();
  const { startRecording, stopRecording, isRecording, transcript, error: sttError } = useSTT();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
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

  const showToast = (message, type = "success") => {
    setToastMessage(message);
    setTimeout(() => setToastMessage(""), 3000);
  };

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage = {
      id: Date.now(),
      type: "user",
      content: inputMessage,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputMessage("");
    setIsLoading(true);

    // 시뮬레이션을 위한 지연
    setTimeout(() => {
      const botResponse = generateBotResponse(inputMessage);
      setMessages((prev) => [...prev, botResponse]);
      setIsLoading(false);
    }, 1500);
  };

  const generateBotResponse = (query) => {
    const responses = {
      verification: {
        content: `📚 **조선왕조실록 기반 답변**

"${query}"에 대한 검색 결과입니다.

**세종실록 12권, 세종 3년 5월 15일**
내시부(內侍府)의 제도를 개편하여 내시의 정원을 30명으로 정하고, 각각의 직무를 명확히 하였다. 내시는 왕의 측근에서 궁중 사무를 담당하며...

**출처**: 조선왕조실록 > 세종실록 > 세종 3년 5월 15일
**신뢰도**: 95%
**관련 키워드**: 내시부, 궁중제도, 세종대왕`,
        keywords: ["내시부", "궁중제도", "세종대왕", "조선왕조실록", "세종실록"],
        sources: ["세종실록 12권", "경국대전"],
      },
      creative: {
        content: `✨ **창작 지원 답변**

"${query}"를 바탕으로 한 창작 아이디어입니다.

**시놉시스 제안**:
세종 3년, 궁중 개혁의 바람이 불던 시기. 젊은 내시 김응룡은 새로운 제도 개편의 중심에 서게 되는데...

**주요 갈등 요소**:
- 기존 세력과 신진 세력 간의 대립
- 왕의 개혁 의지와 현실적 제약
- 개인의 성장과 역사적 사명감

**추천 참고 사료**: 세종실록, 경국대전, 승정원일기`,
        keywords: ["창작", "시놉시스", "갈등구조", "캐릭터", "세종시대"],
        sources: ["세종실록", "승정원일기"],
      },
    };

    const response = responses[chatMode];
    return {
      id: Date.now() + 1,
      type: "bot",
      content: response.content,
      timestamp: new Date(),
      keywords: response.keywords,
      sources: response.sources,
    };
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

  // TTS 기능 구현 - 실제 음성 출력
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
      showToast("음성 출력이 완료되었습니다!");
    } catch (error) {
      console.error("TTS 오류:", error);
      showToast("음성 출력에 실패했습니다.", "error");
    } finally {
      setIsSpeaking(false);
    }
  };

  // STT 기능 구현 - 실제 음성 인식
  const toggleListening = async () => {
    if (isRecording) {
      try {
        await stopRecording();
        showToast("음성 인식을 중지했습니다.");
      } catch (error) {
        console.error("STT 중지 오류:", error);
        showToast("음성 인식 중지에 실패했습니다.", "error");
      }
    } else {
      try {
        await startRecording();
        showToast("음성 인식을 시작합니다. 말씀해 주세요!", "info");
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
  };

  const suggestedQuestions = [
    "세종대왕이 가장 좋아한 음식은 무엇인가요?",
    "조선시대 궁중의 하루 일과는 어떠했나요?",
    "임진왜란 당시 의병 활동은 어떠했나요?",
    "영조의 균역법 개혁 배경을 알려주세요",
    "정조의 수원화성 건설 이유는 무엇인가요?",
  ];

  return (
    <div className="chatbot-page">
      {/* 토스트 메시지 */}
      {toastMessage && (
        <div
          className={`toast-message ${
            toastMessage.includes("오류") || toastMessage.includes("실패") ? "error" : "success"
          }`}>
          {toastMessage}
        </div>
      )}

      <div className="chat-header">
        <div className="chat-title">
          <h1>역사 AI 챗봇</h1>
          <p>조선왕조실록 기반 질의응답 및 창작 지원</p>
        </div>

        <div className="chat-modes">
          <button
            className={`mode-btn ${chatMode === "verification" ? "active" : ""}`}
            onClick={() => setChatMode("verification")}>
            📚 고증 검증
          </button>
          <button
            className={`mode-btn ${chatMode === "creative" ? "active" : ""}`}
            onClick={() => setChatMode("creative")}>
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
                      <button
                        key={index}
                        className="keyword-btn"
                        onClick={() => handleKeywordClick(keyword)}>
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
                  <button
                    className={`action-btn ${isSpeaking ? "speaking" : ""}`}
                    onClick={() => handleSpeakMessage(message.content)}
                    title="음성으로 듣기"
                    disabled={isSpeaking}>
                    <Volume2 size={16} />
                  </button>
                  <button
                    className="action-btn"
                    onClick={() => handleCopyMessage(message.content)}
                    title="복사하기">
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

        <div className="suggested-questions">
          <h3>추천 질문</h3>
          <div className="questions-list">
            {suggestedQuestions.map((question, index) => (
              <button
                key={index}
                className="suggestion-btn"
                onClick={() => setInputMessage(question)}>
                {question}
              </button>
            ))}
          </div>
        </div>

        <div className="chat-input-container">
          <div className="input-actions">
            <button className="action-btn" onClick={handleReset} title="대화 초기화">
              <RotateCcw size={18} />
            </button>
            <button
              className={`action-btn ${isRecording ? "recording" : ""}`}
              onClick={toggleListening}
              title={isRecording ? "음성 입력 중지" : "음성 입력 시작"}
              disabled={isLoading}>
              {isRecording ? <MicOff size={18} /> : <Mic size={18} />}
            </button>
          </div>

          <div className="input-wrapper">
            <textarea
              ref={inputRef}
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder={`${
                chatMode === "verification"
                  ? "역사적 사실에 대해 질문해보세요..."
                  : "창작하고 싶은 내용을 말씀해주세요..."
              }`}
              rows="1"
              className="chat-input"
              disabled={isRecording}
            />
            <button
              className="send-btn"
              onClick={handleSendMessage}
              disabled={!inputMessage.trim() || isLoading || isRecording}>
              <Send size={18} />
            </button>
          </div>

          {/* 음성 인식 상태 표시 */}
          {isRecording && (
            <div className="recording-indicator">
              <div className="recording-animation"></div>
              <span>음성을 인식하고 있습니다...</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default ChatbotPage;
