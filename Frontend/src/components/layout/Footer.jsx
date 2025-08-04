import "@/styles/components/Footer.css";

function Footer() {
  return (
    <footer className="footer">
      <div className="footer-content">
        <div>© 2025 역사로(HistPath) - 국사편찬위원회 조선왕조실록 기반</div>
        <div className="footer-links">
          <a href="/privacy">개인정보처리방침</a>
          <a href="/terms">이용약관</a>
          <a href="/credits">크레딧</a>
        </div>
      </div>
    </footer>
  );
}

export default Footer;
