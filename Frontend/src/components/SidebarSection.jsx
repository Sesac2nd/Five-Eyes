function SidebarSection({ title, children }) {
  return (
    <div className="sidebar-section">
      <div className="section-title">{title}</div>
      {children}
    </div>
  );
}
export default SidebarSection;
