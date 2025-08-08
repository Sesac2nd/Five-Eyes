import { Link } from "react-router-dom";
import { Menu, HelpCircle } from "lucide-react";
import "@/styles/components/Header.css";
import { useDarkMode } from "@/contexts/DarkModeContext"; // 경로 조절 필요

import DarkIcon from '@/assets/icons/icon-dark.svg';   // 흰색/다크모드용 아이콘
import LightIcon from '@/assets/icons/icon-light.svg'; // 검정/라이트모드용 아이콘

function Header({ toggleSidebar }) {
  const { isDarkMode } = useDarkMode();

  return (
    <header className="header">
      <button className="hamburger-btn" onClick={toggleSidebar} aria-label="메뉴 열기">
        <Menu size={24} />
      </button>

      <Link to="/" className="logo">
         <img 
           src={isDarkMode ? DarkIcon : LightIcon} 
           alt="아이콘" 
           className="header-icon"
         /> 
      </Link>

      <div className="header-actions">
        <Link to="/help" className="help-btn" aria-label="도움말">
          <HelpCircle size={20} />
        </Link>
      </div>
    </header>
  );
}

export default Header;
