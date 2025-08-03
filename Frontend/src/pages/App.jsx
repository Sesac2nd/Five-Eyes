import React, { useState } from 'react';
import { Routes, Route, useNavigate } from 'react-router-dom';
import Header from '../components/Header';
import Sidebar from '../components/Sidebar';
import MainContent from './MainContent';
import ResultsPage from './ResultsPage';
import Footer from '../components/Footer';

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [searchInput, setSearchInput] = useState('');
  const navigate = useNavigate();

  const toggleSidebar = () => setSidebarOpen(!sidebarOpen);
  const closeSidebar = () => setSidebarOpen(false);

  // 검색 실행: 검색어가 있으면 결과 페이지로 이동 + 사이드바 닫기
  const handleSearch = () => {
    const trimmed = searchInput.trim();
    if (trimmed) {
      navigate('/results?query=' + encodeURIComponent(trimmed));
      closeSidebar();
    }
  };

  const handleInputKeyPress = (e) => {
    if (e.key === "Enter") handleSearch();
  };

  return (
    <div>
      <Header onHamburgerClick={toggleSidebar} />
      <Sidebar open={sidebarOpen} onClose={closeSidebar} />

      {/* 오버레이는 Sidebar 내에서 처리하므로 중복 제거 */}
      {/* {sidebarOpen && <div className="overlay" onClick={closeSidebar} />} */}

      <Routes>
        <Route
          path="/"
          element={
            <MainContent
              searchValue={searchInput}
              onInputChange={e => setSearchInput(e.target.value)}
              onSearch={handleSearch}
              onInputKeyPress={handleInputKeyPress}
            />
          }
        />
        <Route path="/results" element={<ResultsPage />} />
      </Routes>

      <Footer />
    </div>
  );
}

export default App;
