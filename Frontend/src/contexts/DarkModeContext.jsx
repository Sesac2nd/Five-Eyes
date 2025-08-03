import { createContext, useContext, useState, useEffect } from "react";

// Context에 기본값 제공
const DarkModeContext = createContext({
  isDarkMode: false,
  toggleDarkMode: () => {},
});

export const useDarkMode = () => {
  const context = useContext(DarkModeContext);
  if (!context) {
    throw new Error("useDarkMode must be used within a DarkModeProvider");
  }
  return context;
};

export const DarkModeProvider = ({ children }) => {
  const [isDarkMode, setIsDarkMode] = useState(() => {
    // localStorage에서 저장된 설정 불러오기
    const saved = localStorage.getItem("darkMode");
    if (saved !== null) {
      return JSON.parse(saved);
    }
    // 저장된 설정이 없으면 기본값 라이트모드(false)로 설정
    return false;
  });

  const toggleDarkMode = () => {
    setIsDarkMode((prev) => {
      const newValue = !prev;
      localStorage.setItem("darkMode", JSON.stringify(newValue));
      return newValue;
    });
  };

  // 다크모드 상태에 따라 HTML에 클래스 추가/제거
  useEffect(() => {
    const root = document.documentElement;
    if (isDarkMode) {
      root.classList.add("dark");
    } else {
      root.classList.remove("dark");
    }
  }, [isDarkMode]);

  const value = {
    isDarkMode,
    toggleDarkMode,
  };

  return <DarkModeContext.Provider value={value}>{children}</DarkModeContext.Provider>;
};
