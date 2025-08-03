// src/routes/OcrPageWrapper.jsx
import { useEffect } from "react";
import OcrPage from "@/pages/OcrPage";
import { setPageTitle } from "@/utils";

function OcrPageWrapper() {
  useEffect(() => {
    setPageTitle("OCR 분석");
  }, []);

  return <OcrPage />;
}

export default OcrPageWrapper;
