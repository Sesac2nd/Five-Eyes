import { useState } from "react";
import { Upload, RotateCcw, Play, FileImage, AlertCircle, Focus } from "lucide-react";
import "@/styles/pages/OcrPage.css";

function OcrPage() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [selectedModel, setSelectedModel] = useState("ppocr");
  const [isProcessing, setIsProcessing] = useState(false);
  const [ocrResult, setOcrResult] = useState("");
  const [previewUrl, setPreviewUrl] = useState("");

  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (file) {
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
      setOcrResult(""); // 새 파일 선택시 이전 결과 초기화
    }
  };

  const handleDrop = (event) => {
    event.preventDefault();
    const file = event.dataTransfer.files[0];
    if (file && file.type.startsWith("image/")) {
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
      setOcrResult("");
    }
  };

  const handleDragOver = (event) => {
    event.preventDefault();
  };

  const handleReset = () => {
    setSelectedFile(null);
    setPreviewUrl("");
    setOcrResult("");
    setIsProcessing(false);
  };

  const handleProcess = async () => {
    if (!selectedFile) return;

    setIsProcessing(true);

    try {
      const formData = new FormData();
      formData.append("file", selectedFile);
      // 백엔드의 기본값: engine=\"paddle\" 이므로, 프론트의 선택값을 이에 맞춰 매핑
      // selectedModel: \"ppocr\" | \"azure\"  -> engine: \"paddle\" | \"azure\"
      const engine = selectedModel === "ppocr" ? "paddle" : "azure";
      formData.append("engine", engine);
      formData.append("extract_text_only", "false");
      formData.append("visualization", "true");

      const res = await fetch("/api/ocr/analyze", {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        const errText = await res.text().catch(() => "");
        throw new Error(errText || `OCR 요청 실패: ${res.status}`);
      }

      const data = await res.json();

      // 백엔드 응답 모델(OCRResponse)에 맞춰 텍스트 반영
      // 우선 extracted_text를 결과로 사용
      setOcrResult(data?.extracted_text || "");

      // 필요 시 상태 업데이트 확장 가능:
      // - data.status, data.confidence_score, data.word_count 등

    } catch (error) {
      console.error(error);
      setOcrResult(`분석 중 오류가 발생했습니다: ${error?.message || String(error)}`);
    } finally {
      setIsProcessing(false);
    }
  };


  return (
    <div className="ocr-page">
      <div className="page-header">
        <h1>OCR 문서 분석</h1>
        <p>고문서 이미지에서 한문 텍스트를 추출하고 조선왕조실록과 비교 검증합니다</p>
      </div>

      <div className="ocr-info">
        <h3>사용 안내</h3>
        <div className="info-grid">
          <div className="info-item">
            <h4>1. 이미지 준비</h4>
            <p>조선왕조실록 원문 이미지나 기타 고문서 이미지를 준비하세요.</p>
          </div>
          <div className="info-item">
            <h4>2. 모델 선택</h4>
            <p>한문 텍스트는 PaddleOCR, 일반 문서는 Azure 모델을 권장합니다.</p>
          </div>
          <div className="info-item">
            <h4>3. 결과 확인</h4>
            <p>추출된 텍스트를 실록 데이터베이스와 비교하여 정확도를 확인하세요.</p>
          </div>
        </div>
      </div>

      <div className="ocr-container">
        <div className="ocr-controls">
          <div className="model-selection">
            <h3>분석 모델 선택</h3>
            <div className="model-options">
              <label className="model-option">
                <input
                  type="radio"
                  name="model"
                  value="ppocr"
                  checked={selectedModel === "ppocr"}
                  onChange={(e) => setSelectedModel(e.target.value)}
                />
                <div className="model-info">
                  <span className="model-name">PaddleOCR</span>
                  <span className="model-desc">한문 및 고문서 특화 모델</span>
                </div>
              </label>
              <label className="model-option">
                <input
                  type="radio"
                  name="model"
                  value="azure"
                  checked={selectedModel === "azure"}
                  onChange={(e) => setSelectedModel(e.target.value)}
                />
                <div className="model-info">
                  <span className="model-name">Azure Document Intelligence</span>
                  <span className="model-desc">범용 문서 인식 모델</span>
                </div>
              </label>
            </div>
          </div>

          <div className="action-buttons">
            <label className="btn btn-primary upload-btn">
              <Upload size={16} />
              이미지 업로드
              <input
                type="file"
                accept="image/*"
                onChange={handleFileSelect}
                style={{ display: "none" }}
              />
            </label>
            <button className="btn btn-secondary" onClick={handleReset}>
              <RotateCcw size={16} />
              초기화
            </button>
            <button
              className="btn btn-primary"
              onClick={handleProcess}
              disabled={!selectedFile || isProcessing}>
              {isProcessing ? (
                <>
                  <div className="spinner" />
                  분석 중...
                </>
              ) : (
                <>
                  <Play size={16} />
                  분석 실행
                </>
              )}
            </button>
          </div>
        </div>

        <div className="ocr-content">
          <div className="upload-section">
            <h3>
              <FileImage size={20} />
              원본 이미지
            </h3>
            <div
              className={`upload-area ${selectedFile ? "has-file" : ""}`}
              onDrop={handleDrop}
              onDragOver={handleDragOver}>
              {previewUrl ? (
                <div className="image-preview">
                  <img src={previewUrl} alt="업로드된 이미지" />
                  <div className="file-info">
                    <span>{selectedFile?.name}</span>
                    <span>{(selectedFile?.size / 1024).toFixed(1)} KB</span>
                  </div>
                </div>
              ) : (
                <div className="upload-placeholder">
                  <FileImage size={48} />
                  <p>이미지를 드래그하거나 클릭하여 업로드하세요.</p>
                  <p className="upload-hint">지원 형식: JPG, PNG, GIF (최대 10MB)</p>
                </div>
              )}
            </div>
          </div>

          <div className="result-section">
            <h3>
              {" "}
              <Focus size={20} />
              분석 결과
            </h3>
            <div className="result-area">
              {ocrResult ? (
                <div className="result-content">
                  <pre>{ocrResult}</pre>
                  <div className="result-actions">
                    <button className="btn btn-secondary">실록과 비교</button>
                    <button className="btn btn-secondary">텍스트 복사</button>
                  </div>
                </div>
              ) : (
                <div className="result-placeholder">
                  <AlertCircle size={24} />
                  <p>이미지를 업로드하고 분석을 실행하세요</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default OcrPage;
