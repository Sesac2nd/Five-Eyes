import { Link, useRouteError } from "react-router-dom";
import "@/styles/pages/Pages.css";

function ErrorPage() {
  const error = useRouteError();

  return (
    <div className="error-page">
      <div className="error-content">
        <h1>앗! 오류가 발생했습니다</h1>
        <p>죄송합니다. 예상치 못한 오류가 발생했습니다.</p>

        {error && (
          <div className="error-details">
            <p>
              <strong>오류 메시지:</strong>
            </p>
            <pre>{error.statusText || error.message}</pre>
          </div>
        )}

        <div className="error-actions">
          <Link to="/" className="btn btn-primary">
            홈으로 돌아가기
          </Link>
          <button className="btn btn-secondary" onClick={() => window.location.reload()}>
            페이지 새로고침
          </button>
        </div>
      </div>
    </div>
  );
}

export default ErrorPage;
