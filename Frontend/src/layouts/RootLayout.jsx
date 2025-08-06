import { useState } from "react";
import { Outlet } from "react-router-dom";
import Header from "@/components/layout/Header";
import Sidebar from "@/components/layout/Sidebar";
// import Sidebar from "@/components/Sidebar";
import Footer from "@/components/layout/Footer";
import "@/styles/global.css";

function RootLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const toggleSidebar = () => {
    setSidebarOpen(!sidebarOpen);
  };

  const closeSidebar = () => {
    setSidebarOpen(false);
  };

  return (
    <div className="app">
      <Header toggleSidebar={toggleSidebar} />
      <Sidebar isOpen={sidebarOpen} onClose={closeSidebar} />

      {/* 오버레이 */}
      {sidebarOpen && <div className="overlay active" onClick={closeSidebar} />}

      <main className="main-wrapper">
        <Outlet />
      </main>

      <Footer />
    </div>
  );
}

export default RootLayout;
