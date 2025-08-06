import React, { useEffect } from "react";
import { useLocation } from "react-router-dom";

function MainContent({ searchValue, onInputChange, onSearch, onInputKeyPress }) {
  const location = useLocation();

  useEffect(() => {
    if (location.pathname === "/") {
      onInputChange({ target: { value: "" } });
    }
  }, [location.pathname, onInputChange]);

  return (
    <main className="main-content">
      <div className="logo-main">역사로</div>
      <div className="logo-subtitle">AI가 찾아주는 정확한 역사적 근거</div>
      <div className="search-container">
        <input
          type="text"
          className="search-box"
          value={searchValue}
          onChange={onInputChange}
          onKeyPress={onInputKeyPress}
          placeholder="예: 세종 시대 내시 제도는 어떻게 운영되었나요?"
        />
        <div className="voice-icon">🎤</div>
        <div className="search-icon" onClick={onSearch}>
          🔍
        </div>
      </div>
      <div className="search-buttons">
        <button className="search-btn" onClick={onSearch}>
          고증 검색
        </button>
        <button className="search-btn">랜덤 탐색</button>
      </div>
      <div className="quick-features">
        <div className="quick-feature">
          <span>📸</span>
          <span>이미지 업로드</span>
        </div>
        <div className="quick-feature">
          <span>🎤</span>
          <span>음성 검색</span>
        </div>
        <div className="quick-feature">
          <span>📊</span>
          <span>인기 검색어</span>
        </div>
      </div>
    </main>
  );
}

export default MainContent;
