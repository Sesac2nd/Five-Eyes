function MenuItem({ text, onClick, indent, isExternal }) {
  return (
    <div
      className="menu-item"
      style={indent ? { paddingLeft: 32 } : {}}
      onClick={onClick}
    >
      <div className="menu-text">
        {text}
        {isExternal && <span style={{ marginLeft: 4, color: '#1a73e8' }}>↗</span>}
      </div>
    </div>
  );
}

export default MenuItem;
