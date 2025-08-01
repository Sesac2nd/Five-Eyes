import React from 'react';
import { useLocation } from 'react-router-dom';

function ResultsPage() {
  const location = useLocation();

  // URL 쿼리 파라미터 읽기
  const queryParams = new URLSearchParams(location.search);
  const query = queryParams.get('query') || '';

  return (
    <div className="results-page active">
      <div className="results-header">
        {query
          ? `검색어 "${query}"에 대한 결과 약 1,247개 (0.42초)`
          : '검색어가 없습니다. 검색어를 입력해 주세요.'}
      </div>

      {query ? (
        <>
          {/* 실제 검색 결과 아이템들 */}
          <div className="result-item">
            <div className="result-url">sillok.history.go.kr › 세종실록</div>
            <div className="result-title">세종실록 권12 - 내시부 제도 개편</div>
            <div className="result-snippet">
              세종 3년(1421) 5월 15일...
            </div>
            <div className="result-meta">신뢰도: 95% • 📅 1421.05.15 • 👑 세종</div>
          </div>
          {/* ...더 많은 결과들... */}
        </>
      ) : null}
    </div>
  );
}

export default ResultsPage;
