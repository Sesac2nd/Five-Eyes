import { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import "@/styles/pages/Pages.css";

function SearchResultsPage() {
  const [searchParams] = useSearchParams();
  const query = searchParams.get("q");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (query) {
      // 검색 로직 시뮬레이션
      setTimeout(() => {
        setResults([
          {
            id: 1,
            url: "sillok.history.go.kr › 세종실록",
            title: "세종실록 권12 - 내시부 제도 개편",
            snippet: "세종 3년(1421) 5월 15일. 내시부(內侍府)의 제도를 개편하여 내시의 정원을 30명으로 정하고...",
            reliability: 95,
            date: "1421.05.15",
            king: "세종",
          },
          {
            id: 2,
            url: "sillok.history.go.kr › 세종실록",
            title: "세종실록 권28 - 내시 품계 및 승진 체계",
            snippet: "세종 7년(1425) 2월 3일. 내시의 품계를 정하여 정7품에서 종9품까지로 하고...",
            reliability: 92,
            date: "1425.02.03",
            king: "세종",
          },
        ]);
        setLoading(false);
      }, 1000);
    }
  }, [query]);

  if (loading) {
    return <div className="loading">검색 중...</div>;
  }

  return (
    <div className="search-results-page">
      <div className="results-header">
        <h2>"{query}" 검색 결과</h2>
        <p>약 {results.length}개 결과 (0.42초)</p>
      </div>

      <div className="results-list">
        {results.map((result) => (
          <div key={result.id} className="result-item">
            <div className="result-url">{result.url}</div>
            <h3 className="result-title">{result.title}</h3>
            <p className="result-snippet">{result.snippet}</p>
            <div className="result-meta">
              신뢰도: {result.reliability}% • 📅 {result.date} • 👑 {result.king}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default SearchResultsPage;
