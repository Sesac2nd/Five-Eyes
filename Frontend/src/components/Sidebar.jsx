import React, { useState } from 'react';
import { Link } from "react-router-dom";

function Sidebar({ open, onClose }) {
  // 외부 링크 모달 상태
  const [modalOpen, setModalOpen] = useState(false);
  const [externalUrl, setExternalUrl] = useState('');
  const [externalName, setExternalName] = useState('');

  // 외부 링크 클릭 시 모달 열기
  const handleExternalLinkClick = (url, name) => {
    setExternalUrl(url);
    setExternalName(name);
    setModalOpen(true);
  };

  // 외부 사이트 이동
  const confirmExternalLink = () => {
    window.open(externalUrl, '_blank', 'noopener,noreferrer');
    closeModal();
    onClose();
  };

  const closeModal = () => setModalOpen(false);

  // 사료 출처 목록
  const sources = [
    { name: '조선왕조실록', url: 'http://sillok.history.go.kr' },
    { name: '승정원일기', url: 'http://sjw.history.go.kr' },
    { name: '장서각', url: 'https://kyujanggak.snu.ac.kr' },
    { name: '규장각', url: 'https://kyujanggak.snu.ac.kr' },
  ];

  return (
    <>
      {/* 오버레이 */}
      {open && (
        <div className="overlay"
          onClick={onClose}
          style={{
            position: 'fixed',
            top: 0, left: 0, right: 0, bottom: 0,
            backgroundColor: 'rgba(0,0,0,0.5)',
            zIndex: 99,
          }}
        />
      )}

      {/* 사이드바 */}
      <aside className={`sidebar${open ? " active" : ""}`} style={{
        position: 'fixed',
        top: 0,
        left: open ? '0' : '-250px',
        width: '250px',
        height: '100%',
        backgroundColor: '#fff',
        boxShadow: '2px 0 5px rgba(0,0,0,0.3)',
        transition: 'left 0.3s ease',
        zIndex: 100,
        padding: '1rem',
        overflowY: 'auto',
      }}>
        {/* 닫기 버튼 */}
        <button onClick={onClose} aria-label="사이드바 닫기" style={{
          display: 'block',
          marginBottom: '1.5rem',
          cursor: 'pointer',
          fontWeight: 'bold',
          background: 'none',
          border: 'none',
          fontSize: '1.2rem',
        }}>
          X 닫기
        </button>

        {/* 사이트명 및 설명 (클릭 시 메인으로 이동) */}
        <div onClick={() => { onClose(); }} style={{ cursor: 'pointer', marginBottom: '2rem' }}>
          <Link to="/" style={{ textDecoration: 'none', color: '#333' }}>
            <h2 style={{ margin: 0, fontWeight: 300 }}>역사로 歷史路</h2>
            <p style={{ margin: '0.2rem 0 0 0', fontSize: '0.9rem', color: '#666' }}>
              AI 기반 한국사 고증 검색 플랫폼
            </p>
          </Link>
        </div>

        {/* 주요 기능 */}
        <nav>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 'bold', marginBottom: '0.8rem' }}>주요 기능</h3>
          <ul style={{ listStyle: 'none', paddingLeft: 0, marginBottom: '1.5rem' }}>
            <li style={{ marginBottom: '0.8rem' }}>
              <Link to="/ocr" onClick={onClose} style={{ textDecoration: 'none', color: '#333' }}>
                OCR 페이지
              </Link>
            </li>
            <li style={{ marginBottom: '0.3rem' }}>
              <Link to="/chatbot" onClick={onClose} style={{ textDecoration: 'none', color: '#333' }}>
                챗봇 페이지
              </Link>
            </li>
            <ul style={{ listStyle: 'none', paddingLeft: '1.2rem', marginTop: 0, marginBottom: '1rem' }}>
              <li style={{ marginBottom: '0.5rem' }}>
                <Link to="/chatbot/validation" onClick={onClose} style={{ textDecoration: 'none', color: '#555' }}>
                  고증 검증
                </Link>
              </li>
              <li>
                <Link to="/chatbot/synopsis" onClick={onClose} style={{ textDecoration: 'none', color: '#555' }}>
                  시놉시스 작성 도우미
                </Link>
              </li>
            </ul>
          </ul>

          {/* 사료 출처 */}
          <h3 style={{ fontSize: '1.1rem', fontWeight: 'bold', marginBottom: '0.8rem' }}>사료 출처</h3>
          <ul style={{ listStyle: 'none', paddingLeft: 0, marginBottom: '1.5rem' }}>
            {sources.map(src => (
              <li key={src.name} style={{ marginBottom: '0.8rem' }}>
                <button
                  onClick={() => handleExternalLinkClick(src.url, src.name)}
                  style={{
                    background: 'none',
                    border: 'none',
                    padding: 0,
                    color: '#1a73e8',
                    cursor: 'pointer',
                    fontSize: '1rem',
                    textDecoration: 'underline',
                  }}
                >
                  {src.name}
                </button>
              </li>
            ))}
          </ul>

          {/* 설정 */}
          <h3 style={{ fontSize: '1.1rem', fontWeight: 'bold', marginBottom: '0.8rem' }}>설정</h3>
          <ul style={{ listStyle: 'none', paddingLeft: 0, marginBottom: '0' }}>
            <li style={{ marginBottom: '0.8rem' }}>
              <Link to="/contact" onClick={onClose} style={{ textDecoration: 'none', color: '#333' }}>
                문의하기
              </Link>
            </li>
            <li>
              <Link to="/about" onClick={onClose} style={{ textDecoration: 'none', color: '#333' }}>
                만든이
              </Link>
            </li>
          </ul>
        </nav>
      </aside>

      {/* 외부 링크 확인용 모달 */}
      {modalOpen && (
        <div style={{
          position: 'fixed',
          top: 0, left: 0, right: 0, bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.3)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 2000,
        }}>
          <div style={{
            backgroundColor: '#fff',
            padding: '1.5rem 2rem',
            borderRadius: '8px',
            maxWidth: '320px',
            boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
            textAlign: 'center',
          }}>
            <p style={{ marginBottom: '1rem' }}>
              <strong>{externalName}</strong> 페이지로 이동하시겠습니까?
            </p>
            <div style={{ display: 'flex', justifyContent: 'center', gap: '1rem' }}>
              <button onClick={closeModal} style={{
                padding: '0.5rem 1rem', borderRadius: '4px',
                border: '1px solid #ccc', backgroundColor: '#f0f0f0',
                cursor: 'pointer',
              }}>취소</button>
              <button onClick={confirmExternalLink} style={{
                padding: '0.5rem 1rem', borderRadius: '4px',
                border: 'none', backgroundColor: '#1a73e8',
                color: '#fff', cursor: 'pointer',
              }}>이동</button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

export default Sidebar;
