import { useState, useRef, useEffect } from "react";
import { Send, Mic, MicOff, Volume2, Copy, RotateCcw } from "lucide-react";
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
  const [isListening, setIsListening] = useState(false);
  const [chatMode, setChatMode] = useState("verification"); // verification | creative
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

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
        keywords: ["내시부", "고증", "실록"],  // 강제로 다르게 줌
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
        keywords: ["창작", "스토리", "아이디어"],  // 차별 키워드
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

  const toggleListening = () => {
    setIsListening(!isListening);
    // 실제 구현시 Web Speech API 사용
  };

  const handleSpeakMessage = (content) => {
    // 실제 구현시 Speech Synthesis API 사용
    console.log("Speaking:", content);
  };

  const handleCopyMessage = (content) => {
    navigator.clipboard.writeText(content);
    // 토스트 메시지 표시 가능
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
  };

  const suggestedQuestions = [
    "세종대왕이 가장 좋아한 음식은 무엇인가요?",
    "조선시대 궁중의 하루 일과는 어떠했나요?",
    "임진왜란 당시 의병 활동은 어떠했나요?",
    "영조의 균역법 개혁 배경을 알려주세요",
    "정조의 수원화성 건설 이유는 무엇인가요?",
  ];

  return (
    <div className={`chatbot-page ${chatMode}`}>
      <div className={`chat-header ${chatMode}`}>
        <div className="chat-title">
          <h1>역사 AI 챗봇</h1>
          <p>
            조선왕조실록 기반 질의응답 및 창작 지원{" "}
            <span
              style={{
                marginLeft: 10,
                fontWeight: "bold",
                color: chatMode === "verification" ? "#4285f4" : "#ffa438",
              }}
            >
              {chatMode === "verification" ? "고증 검증 모드" : "창작 도우미 모드"}
            </span>
          </p>
        </div>

        <div className="chat-modes">
          <button
            className={`mode-btn ${
              chatMode === "verification" ? "active verification" : ""
            }`}
            onClick={() => setChatMode("verification")}
          >
            📚 고증 검증
          </button>
          <button
            className={`mode-btn ${
              chatMode === "creative" ? "active creative" : ""
            }`}
            onClick={() => setChatMode("creative")}
          >
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
                        onClick={() => handleKeywordClick(keyword)}
                      >
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
                    className="action-btn"
                    onClick={() => handleSpeakMessage(message.content)}
                    title="음성으로 듣기"
                  >
                    <Volume2 size={16} />
                  </button>
                  <button
                    className="action-btn"
                    onClick={() => handleCopyMessage(message.content)}
                    title="복사하기"
                  >
                    <Copy size={16} />
                  </button>
                </div>
              )}

              <div className="message-time">
                {message.timestamp.toLocaleTimeString()}
              </div>
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
                onClick={() => setInputMessage(question)}
              >
                {question}
              </button>
            ))}
          </div>
        </div>

        <div className="chat-input-container">
          <div className="input-actions">
            <button
              className="action-btn"
              onClick={handleReset}
              title="대화 초기화"
            >
              <RotateCcw size={18} />
            </button>
            <button
              className={`action-btn ${isListening ? "active" : ""}`}
              onClick={toggleListening}
              title="음성 입력"
            >
              {isListening ? <MicOff size={18} /> : <Mic size={18} />}
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
            />
            <button
              className="send-btn"
              onClick={handleSendMessage}
              disabled={!inputMessage.trim() || isLoading}
            >
              <Send size={18} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default ChatbotPage;
