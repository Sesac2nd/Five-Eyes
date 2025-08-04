import "@/styles/pages/Pages.css";

function CreditsPage() {
  const teamMembers = [
    {
      name: "김철수",
      role: "PM & Frontend Developer",
      github: "https://github.com/kimcheolsu",
      description: "React 개발 및 UI/UX 디자인",
    },
    {
      name: "이영희",
      role: "Backend Developer",
      github: "https://github.com/leeyounghee",
      description: "FastAPI 서버 개발 및 데이터베이스 설계",
    },
    {
      name: "박민수",
      role: "AI Engineer",
      github: "https://github.com/parkminsu",
      description: "OCR 모델 및 RAG 시스템 구축",
    },
  ];

  return (
    <div className="credits-page">
      <div className="page-header">
        <h1>🧑‍💻만든이</h1>
        <p>역사로 프로젝트를 만든 팀을 소개합니다</p>
      </div>

      <div className="team-grid">
        {teamMembers.map((member, index) => (
          <div key={index} className="member-card">
            <div className="member-avatar">{member.name.charAt(0)}</div>
            <h3>{member.name}</h3>
            <p className="member-role">{member.role}</p>
            <p className="member-desc">{member.description}</p>
            <a href={member.github} target="_blank" rel="noopener noreferrer" className="github-link">
              GitHub
            </a>
          </div>
        ))}
      </div>

      <div className="project-info">
        <h2>프로젝트 정보</h2>
        <div className="info-grid">
          <div className="info-item">
            <h3>개발 기간</h3>
            <p>2025.07.25  - 2025.08.12 (3주)</p>
          </div>
          <div className="info-item">
            <h3>기술 스택</h3>
            <p>React, FastAPI, Azure AI, PostgreSQL</p>
          </div>
          <div className="info-item">
            <h3>데이터 출처</h3>
            <p>국사편찬위원회 조선왕조실록</p>
          </div>
        </div>
      </div>

      <div className="disclaimer">
        <h2>서비스 원칙 및 책임 한계</h2>
        <div className="disclaimer-content">
          <p>본 서비스는 교육 및 연구 목적으로 제작되었습니다.</p>
          <p>AI가 제공하는 정보의 정확성에 대해서는 사용자가 최종 검증해야 합니다.</p>
          <p>조선왕조실록 원문과 번역에 오류가 있을 수 있으니 중요한 내용은 원전을 확인하시기 바랍니다.</p>
          <p>상업적 목적으로 사용할 경우 별도 허가가 필요할 수 있습니다.</p>
        </div>
      </div>
    </div>
  );
}

export default CreditsPage;
