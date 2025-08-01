import React from 'react';
import { Link } from 'react-router-dom';  // Link 임포트 추가

function Header({ onHamburgerClick }) {
  return (
    <header className="header">
      <div className="hamburger" onClick={onHamburgerClick}>
        <div className="hamburger-line"></div>
        <div className="hamburger-line"></div>
        <div className="hamburger-line"></div>
      </div>

      {/* "역사로"를 Link로 감싸 홈으로 이동 가능하도록 변경 */}
      <Link to="/" className="logo" style={{ textDecoration: 'none', color: 'inherit' }}>
        역사로
      </Link>

      <div className="user-menu">
        <button className="login-btn">로그인</button>
      </div>
    </header>
  );
}

export default Header;
