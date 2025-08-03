import "@/styles/pages/Pages.css";

function HelpPage() {
  return (
    <div className="help-page">
      <div className="page-header">
        <h1>도움말</h1>
        <p>역사로 서비스 사용법을 안내합니다</p>
      </div>

      <div className="help-content">
        <section className="help-section">
          <h2>🔍 고증 검색 사용법</h2>
          <div className="help-item">
            <h3>자연어 검색</h3>
            <p>"세종대왕이 한글을 만든 이유는?" 같은 자연스러운 질문으로 검색하세요.</p>
          </div>
          <div className="help-item">
            <h3>키워드 검색</h3>
            <p>인물명, 사건명, 제도명 등의 키워드로도 검색 가능합니다.</p>
          </div>
        </section>

        <section className="help-section">
          <h2>📸 OCR 분석 사용법</h2>
          <div className="help-item">
            <h3>이미지 업로드</h3>
            <p>조선왕조실록 원문 이미지나 고문서 이미지를 업로드하세요.</p>
          </div>
          <div className="help-item">
            <h3>모델 선택</h3>
            <p>한문 텍스트는 PaddleOCR, 일반 문서는 Azure 모델을 권장합니다.</p>
          </div>
        </section>

        <section className="help-section">
          <h2>🤖 챗봇 사용법</h2>
          <div className="help-item">
            <h3>고증 검증 모드</h3>
            <p>역사적 사실에 대한 정확한 정보를 제공합니다.</p>
          </div>
          <div className="help-item">
            <h3>창작 도우미 모드</h3>
            <p>소설, 시나리오 등 창작 활동을 지원합니다.</p>
          </div>
        </section>
      </div>
    </div>
  );
}

export default HelpPage;
