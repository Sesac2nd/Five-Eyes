function ExternalLinkModal({ url, onClose }) {
  function goToSite() {
    window.open(url, '_blank', 'noopener,noreferrer');
    onClose();
  }
  return (
    <div className="modal-overlay">
      <div className="modal-window">
        <p>해당 사이트(외부 페이지)로 이동하시겠습니까?</p>
        <div style={{ marginTop: '16px', display: 'flex', justifyContent: 'flex-end', gap: '10px'}}>
          <button onClick={onClose}>취소</button>
          <button onClick={goToSite}>이동</button>
        </div>
      </div>
    </div>
  );
}
export default ExternalLinkModal;
