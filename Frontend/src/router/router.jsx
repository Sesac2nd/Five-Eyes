// src/router/router.jsx
import RootLayout from "@/layouts/RootLayout";
import { HelpPage, CreditsPage, Error } from "@/pages";
import { configRoutes, getNavigationItems } from "@/utils";
import { createBrowserRouter } from "react-router-dom";

// 분리된 컴포넌트 import (Wrapper 패턴)
import HomePageWrapper from "@/routes/HomePageWrapper";
import OcrPageWrapper from "@/routes/OcrPageWrapper";
import ChatbotPageWrapper from "@/routes/ChatbotPageWrapper";
import SearchResultsPageWrapper from "@/routes/SearchResultsPageWrapper";

/** @type {import('react-router-dom').RouteObject[]} */
const navigation = [
  {
    text: "메인",
    index: true,
    element: <HomePageWrapper />,
  },
  {
    text: "OCR 분석",
    path: "/ocr",
    element: <OcrPageWrapper />,
    icon: "📸",
    description: "고문서 이미지 텍스트 추출",
  },
  {
    text: "챗봇",
    path: "/chatbot",
    element: <ChatbotPageWrapper />,
    icon: "🤖",
    description: "AI 역사 상담 및 창작 지원",
  },
  {
    text: "검색 결과",
    path: "/search",
    element: <SearchResultsPageWrapper />,
    hideInMenu: true, // 메뉴에서 숨김
  },
  {
    text: "도움말",
    path: "/help",
    element: <HelpPage />,
    icon: "❓",
    description: "서비스 사용법 안내",
  },
  {
    text: "만든 이",
    path: "/credits",
    element: <CreditsPage />,
    icon: "👥",
    description: "프로젝트 팀 소개",
  },
];

/** @type {import('react-router-dom').RouteObject[]} */
export const routes = [
  {
    path: "/",
    element: <RootLayout />,
    errorElement: <Error />,
    children: configRoutes(navigation),
  },
];

const router = createBrowserRouter(routes, {
  basename: import.meta.env.BASE_URL,
});

export default router;
export const navigationItems = getNavigationItems(navigation);
