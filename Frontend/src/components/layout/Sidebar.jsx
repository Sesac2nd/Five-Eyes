import { Link } from "react-router-dom";
import {
  BookMarked,
  Search,
  Users,
  Lightbulb,
  Settings,
  FileText,
  Bot,
  Text,
  BarChart3,
  Crown,
  Scroll,
  FileX,
  File,
  Moon,
  Sun,
  Bell,
  HelpCircle,
  ExternalLink,
} from "lucide-react";
import { useDarkMode } from "@/contexts/DarkModeContext";
import "@/styles/components/Sidebar.css";
import Icon from '@/assets/icons/icon.svg';

function Sidebar({ isOpen, onClose }) {
  const { isDarkMode, toggleDarkMode } = useDarkMode();

  const handleMenuClick = () => {
    // 메뉴 클릭 시 시각적 피드백
    onClose();
  };

  const handleDarkModeToggle = () => {
    toggleDarkMode();
  };

  const handleExternalLink = (url) => {
    if (confirm("외부 사이트로 이동하시겠습니까?")) {
      window.open(url, "_blank");
    }
  };

  return (
    <aside className={`sidebar ${isOpen ? "active" : ""}`}>
      <div className="sidebar-header">
        <div className="sidebar-title">
          {" "}
          <img src={Icon} alt="아이콘" className="sidebar-icon"/> 
          <span className="sidebar-title-text">역사로 歷史路</span>
        </div>
        <div className="sidebar-subtitle">AI 기반 한국사 고증 검색 플랫폼</div>
      </div>

      <div className="sidebar-section">
        <div className="section-title">
          <Lightbulb size={20} />
          주요 기능
        </div>
        {/* <Link to="/search" className="menu-item" onClick={handleMenuClick}>
          <div className="menu-icon">
            <Search size={20} />
          </div>
          <div>
            <div className="menu-text">고증 검색</div>
            <div className="menu-desc">자연어로 역사적 사실 검색</div>
          </div>
        </Link> */}
        <Link to="/chatbot" className="menu-item" onClick={handleMenuClick}>
          <div className="menu-icon">
            <Bot size={20} />
          </div>
          <div>
            <div className="menu-text">챗봇</div>
            <div className="menu-desc">AI 역사 상담 및 창작 도우미</div>
          </div>
        </Link>
        <Link to="/ocr" className="menu-item" onClick={handleMenuClick}>
          <div className="menu-icon">
            <Text size={20} />
          </div>
          <div>
            <div className="menu-text">OCR 분석</div>
            <div className="menu-desc">고문서 이미지 텍스트 추출</div>
          </div>
        </Link>
        {/* <div className="menu-item">
          <div className="menu-icon">
            <BarChart3 size={20} />
          </div>
          <div>
            <div className="menu-text">리포트 생성</div>
            <div className="menu-desc">고증 근거 PDF 다운로드</div>
          </div>
        </div> */}
      </div>

      <div className="sidebar-section">
        <div className="section-title">
          <Scroll size={20} />
          사료 출처
        </div>
        <div
          className="menu-item"
          onClick={() => handleExternalLink("https://sillok.history.go.kr")}>
          <div className="menu-icon">
            <ExternalLink size={20} />
          </div>
          <div>
            <div className="menu-text">조선왕조실록</div>
            <div className="menu-desc">472년간의 공식 기록</div>
          </div>
        </div>
        <div className="menu-item" onClick={() => handleExternalLink("https://sjw.history.go.kr")}>
          <div className="menu-icon">
            <ExternalLink size={20} />
          </div>
          <div>
            <div className="menu-text">승정원일기</div>
            <div className="menu-desc">왕의 일상 기록</div>
          </div>
        </div>
        <div className="menu-item" onClick={() => handleExternalLink("https://jsg.aks.ac.kr")}>
          <div className="menu-icon">
            <ExternalLink size={20} />
          </div>
          <div>
            <div className="menu-text">장서각</div>
            <div className="menu-desc">한국학중앙연구원 디지털장서각</div>
          </div>
        </div>
        <div
          className="menu-item"
          onClick={() => handleExternalLink("https://kyujanggak.snu.ac.kr")}>
          <div className="menu-icon">
            <ExternalLink size={20} />
          </div>
          <div>
            <div className="menu-text">규장각</div>
            <div className="menu-desc">서울대학교 규장각한국학연구원</div>
          </div>
        </div>
      </div>

      <div className="sidebar-section">
        <div className="section-title">
          {" "}
          <Settings size={20} /> 설정
        </div>
        {/* 다크모드 토글 버튼 - 수정된 부분 */}
        <div className="menu-item" onClick={handleDarkModeToggle}>
          <div className="menu-icon">{isDarkMode ? <Sun size={20} /> : <Moon size={20} />}</div>
          <div>
            <div className="menu-text">{isDarkMode ? "라이트 모드" : "다크 모드"}</div>
            <div className="menu-desc">
              {isDarkMode ? "밝은 테마로 전환" : "어두운 테마로 전환"}
            </div>
          </div>
        </div>
        {/* <div className="menu-item">
          <div className="menu-icon">
            <Bell size={20} />
          </div>
          <div>
            <div className="menu-text">알림 설정</div>
          </div>
        </div> */}
        <Link to="/help" className="menu-item" onClick={handleMenuClick}>
          <div className="menu-icon">
            <HelpCircle size={20} />
          </div>
          <div>
            <div className="menu-text">도움말</div>
          </div>
        </Link>
        <Link to="/credits" className="menu-item" onClick={handleMenuClick}>
          <div className="menu-icon">
            <Users size={20} />
          </div>
          <div>
            <div className="menu-text">만든이</div>
          </div>
        </Link>
      </div>
    </aside>
  );
}

export default Sidebar;
