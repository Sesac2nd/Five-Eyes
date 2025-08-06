import { useState, useEffect } from "react";

/**
 * 다크모드 상태를 관리하는 커스텀 훅
 * @returns {Object} { isDarkMode, toggleDarkMode, setDarkMode }
 */
export const useDarkMode = () => {
  const [isDarkMode, setIsDarkMode] = useState(() => {
    // localStorage에서 저장된 설정 불러오기
    const saved = localStorage.getItem("darkMode");
    if (saved !== null) {
      return JSON.parse(saved);
    }
    // 저장된 설정이 없으면 시스템 설정 따르기
    return window.matchMedia("(prefers-color-scheme: dark)").matches;
  });

  const toggleDarkMode = () => {
    setIsDarkMode((prev) => {
      const newValue = !prev;
      localStorage.setItem("darkMode", JSON.stringify(newValue));
      return newValue;
    });
  };

  const setDarkMode = (value) => {
    setIsDarkMode(value);
    localStorage.setItem("darkMode", JSON.stringify(value));
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

  // 시스템 다크모드 변경 감지
  useEffect(() => {
    const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");
    const handleChange = (e) => {
      // 사용자가 수동으로 설정하지 않은 경우만 시스템 설정 따르기
      const saved = localStorage.getItem("darkMode");
      if (saved === null) {
        setIsDarkMode(e.matches);
      }
    };

    mediaQuery.addEventListener("change", handleChange);
    return () => mediaQuery.removeEventListener("change", handleChange);
  }, []);

  return {
    isDarkMode,
    toggleDarkMode,
    setDarkMode,
  };
};
