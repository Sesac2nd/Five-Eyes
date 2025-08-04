// src/routes/ChatbotPageWrapper.jsx
import { useEffect } from "react";
import ChatbotPage from "@/pages/ChatbotPage";
import { setPageTitle } from "@/utils";

function ChatbotPageWrapper() {
  useEffect(() => {
    setPageTitle("AI 챗봇");
  }, []);

  return <ChatbotPage />;
}

export default ChatbotPageWrapper;
