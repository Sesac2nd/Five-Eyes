import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Search, Mic, Camera, BarChart3, TrendingUp } from "lucide-react";
import "@/styles/pages/HomePage.css";

function HomePage() {
  const [searchQuery, setSearchQuery] = useState("");
  const navigate = useNavigate();

  const handleSearch = () => {
    if (searchQuery.trim()) {
      navigate(`/search?q=${encodeURIComponent(searchQuery)}`);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter") {
      handleSearch();
    }
  };

  const handleRandomSearch = () => {
    const randomQueries = [
      "세종대왕이 가장 좋아한 음식은?",
      "조선시대 궁중의 하루 일과는?",
      "임진왜란 당시 의병 활동은?",
      "영조의 균역법 개혁 배경은?",
      "정조의 수원화성 건설 이유는?",
    ];
    const randomQuery = randomQueries[Math.floor(Math.random() * randomQueries.length)];
    setSearchQuery(randomQuery);
    navigate(`/search?q=${encodeURIComponent(randomQuery)}`);
  };

  return (
    <div className="home-page">
      <div className="home-content">
        <div className="logo-section">
          <h1 className="logo-main">역사로</h1>
          <p className="logo-subtitle">AI가 찾아주는 정확한 역사적 근거</p>
        </div>

        <div className="search-section">
          <div className="search-container">
            <input
              type="text"
              className="search-box"
              placeholder="예: 세종 시대 내시 제도는 어떻게 운영되었나요?"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyPress={handleKeyPress}
            />
            <button className="voice-icon" aria-label="음성 검색">
              <Mic size={16} />
            </button>
            <button className="search-icon" onClick={handleSearch} aria-label="검색">
              <Search size={18} />
            </button>
          </div>

          <div className="search-buttons">
            <button className="btn btn-primary" onClick={handleSearch}>
              고증 검색
            </button>
            <button className="btn btn-secondary" onClick={handleRandomSearch}>
              랜덤 탐색
            </button>
          </div>
        </div>

        <div className="quick-features">
          <button className="quick-feature" onClick={() => navigate("/ocr")}>
            <Camera size={16} />
            <span>이미지 업로드</span>
          </button>
          <button className="quick-feature">
            <Mic size={16} />
            <span>음성 검색</span>
          </button>
          <button className="quick-feature">
            <TrendingUp size={16} />
            <span> 인기 검색어</span>
          </button>
        </div>

        <div className="popular-searches">
          <h3>
            <Search size={18} /> 인기 검색어 Top5
          </h3>
          <div className="search-tags">
            <button className="search-tag" onClick={() => setSearchQuery("세종대왕 한글 창제")}>
              세종대왕 한글 창제
            </button>
            <button className="search-tag" onClick={() => setSearchQuery("조선시대 과거제도")}>
              조선시대 과거제도
            </button>
            <button className="search-tag" onClick={() => setSearchQuery("임진왜란 이순신")}>
              임진왜란 이순신
            </button>
            <button className="search-tag" onClick={() => setSearchQuery("영조 탕평책")}>
              영조 탕평책
            </button>
            <button className="search-tag" onClick={() => setSearchQuery("정조 규장각")}>
              정조 규장각
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default HomePage;
