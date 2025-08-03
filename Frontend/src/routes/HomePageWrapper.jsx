// src/routes/HomePageWrapper.jsx
import { useEffect } from "react";
import HomePage from "@/pages/HomePage";
import { setPageTitle } from "@/utils";

function HomePageWrapper() {
  useEffect(() => {
    setPageTitle("메인");
  }, []);

  return <HomePage />;
}

export default HomePageWrapper;
