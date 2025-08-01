import React from 'react';
import { Link } from "react-router-dom";

function Sidebar({ open, onClose }) {
  return (
    <>
      {/* 사이드바 오버레이(검은 반투명 배경) - 사이드바가 열렸을 때만 보이고, 클릭하면 닫힘 */}
      {open && <div className="overlay" onClick={onClose} style={{
        position: 'fixed',
        top: 0, left: 0, right: 0, bottom: 0,
        backgroundColor: 'rgba(0,0,0,0.5)',
        zIndex: 99,
      }} />}

      {/* 실제 사이드바 */}
      <aside className={`sidebar${open ? " active" : ""}`} style={{
        position: 'fixed',
        top: 0,
        left: open ? '0' : '-250px', // 슬라이드 오픈 애니메이션 간단 처리
        width: '250px',
        height: '100%',
        backgroundColor: '#fff',
        boxShadow: '2px 0 5px rgba(0,0,0,0.3)',
        transition: 'left 0.3s ease',
        zIndex: 100,
        padding: '1rem',
      }}>
        {/* 닫기 버튼 */}
        <button onClick={onClose} aria-label="사이드바 닫기" style={{
          display: 'block',
          marginBottom: '1rem',
          cursor: 'pointer',
        }}>
          X 닫기
        </button>

        {/* 네비게이션 메뉴 */}
        <nav>
          <ul style={{listStyle: 'none', padding: 0}}>
            <li>
              <Link to="/" onClick={onClose}>메인으로 이동</Link>
            </li>
            <li>
              <Link to="/results" onClick={onClose}>결과 페이지 가기</Link>
            </li>
          </ul>
        </nav>

        {/* 여기에 필요하면 추가 내용 작성 */}
      </aside>
    </>
  );
}

export default Sidebar;
