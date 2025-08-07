import { Link } from "react-router-dom";
import { Menu, HelpCircle } from "lucide-react";
import "@/styles/components/Header.css";
import Icon from '@/assets/icons/icon.svg';


function Header({ toggleSidebar }) {
  return (
    <header className="header">
      <button className="hamburger-btn" onClick={toggleSidebar} aria-label="메뉴 열기">
        <Menu size={24} />
      </button>

      <Link to="/" className="logo">
         <img src={Icon} alt="아이콘" className="header-icon"/> 
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
