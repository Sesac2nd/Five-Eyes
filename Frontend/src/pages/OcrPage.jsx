// Frontend/src/pages/OcrPage.jsx - localStorage 저장 + 분석 이미지 표기 기능
import { useState, useEffect, useRef } from "react";
import {
  Upload,
  RotateCcw,
  Play,
  FileImage,
  AlertCircle,
  Focus,
  Clock,
  CheckCircle,
  Image as ImageIcon,
  Eye,
} from "lucide-react";
import "@/styles/pages/OcrPage.css";

function OcrPage() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [selectedModel, setSelectedModel] = useState("ppocr");
  const [isProcessing, setIsProcessing] = useState(false);
  const [ocrResult, setOcrResult] = useState("");
  const [previewUrl, setPreviewUrl] = useState("");

  // 비동기 관련 상태
  const [currentAnalysisId, setCurrentAnalysisId] = useState(null);
  const [progressPercentage, setProgressPercentage] = useState(0);
  const [currentStep, setCurrentStep] = useState("");
  const [visualizationUrl, setVisualizationUrl] = useState(null);
  const [showVisualization, setShowVisualization] = useState(false);

  // 분석 결과 저장
  const [analysisResults, setAnalysisResults] = useState({});

  const pollingIntervalRef = useRef(null);

  // localStorage 키들
  const STORAGE_KEYS = {
    currentAnalysis: "currentOcrAnalysis",
    analysisResults: "ocrAnalysisResults",
    activeAnalyses: "ocrActiveAnalyses",
  };

  // 컴포넌트 마운트 시 localStorage에서 데이터 복원
  useEffect(() => {
    // 저장된 분석 결과들 복원
    const savedResults = localStorage.getItem(STORAGE_KEYS.analysisResults);
    if (savedResults) {
      try {
        setAnalysisResults(JSON.parse(savedResults));
      } catch (e) {
        console.warn("저장된 분석 결과 파싱 실패:", e);
      }
    }

    // 진행 중인 분석 복원
    const savedAnalysisId = localStorage.getItem(STORAGE_KEYS.currentAnalysis);
    if (savedAnalysisId) {
      setCurrentAnalysisId(savedAnalysisId);
      setIsProcessing(true);
      checkAnalysisStatus(savedAnalysisId);
      console.log(`🔄 진행 중인 분석 복원: ${savedAnalysisId}`);
    }
  }, []);

  // analysisResults 변경 시 localStorage에 저장
  useEffect(() => {
    if (Object.keys(analysisResults).length > 0) {
      localStorage.setItem(STORAGE_KEYS.analysisResults, JSON.stringify(analysisResults));
    }
  }, [analysisResults]);

  const saveAnalysisResult = (analysisId, data) => {
    setAnalysisResults((prev) => ({
      ...prev,
      [analysisId]: {
        ...data,
        savedAt: new Date().toISOString(),
      },
    }));
  };

  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (file) {
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
      setOcrResult("");
      setVisualizationUrl(null);
      setShowVisualization(false);
    }
  };

  const handleDrop = (event) => {
    event.preventDefault();
    const file = event.dataTransfer.files[0];
    if (file && file.type.startsWith("image/")) {
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
      setOcrResult("");
      setVisualizationUrl(null);
      setShowVisualization(false);
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
    setCurrentAnalysisId(null);
    setProgressPercentage(0);
    setCurrentStep("");
    setVisualizationUrl(null);
    setShowVisualization(false);
    localStorage.removeItem(STORAGE_KEYS.currentAnalysis);

    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
    }
  };

  const checkAnalysisStatus = async (analysisId) => {
    try {
      const response = await fetch(`/api/ocr/status/${analysisId}`);
      if (!response.ok) throw new Error(`상태 확인 실패: ${response.status}`);

      const statusData = await response.json();
      setProgressPercentage(statusData.progress_percentage);
      setCurrentStep(statusData.current_step || "");

      console.log(`📊 상태: ${statusData.progress_percentage}% - ${statusData.current_step}`);

      if (statusData.status === "completed") {
        setIsProcessing(false);
        localStorage.removeItem(STORAGE_KEYS.currentAnalysis);
        fetchAnalysisResult(analysisId);
        if (pollingIntervalRef.current) {
          clearInterval(pollingIntervalRef.current);
          pollingIntervalRef.current = null;
        }
      } else if (statusData.status === "failed") {
        setIsProcessing(false);
        setOcrResult(`❌ 분석 실패: ${statusData.error_message || "알 수 없는 오류"}`);
        localStorage.removeItem(STORAGE_KEYS.currentAnalysis);
        if (pollingIntervalRef.current) {
          clearInterval(pollingIntervalRef.current);
          pollingIntervalRef.current = null;
        }
      }
    } catch (error) {
      console.error("❌ 상태 확인 오류:", error);
    }
  };

  const fetchAnalysisResult = async (analysisId) => {
    try {
      const response = await fetch(`/api/ocr/result/${analysisId}`);
      if (!response.ok) throw new Error(`결과 조회 실패: ${response.status}`);

      const resultData = await response.json();
      setOcrResult(resultData.extracted_text || "추출된 텍스트가 없습니다.");

      if (resultData.visualization_url) {
        setVisualizationUrl(resultData.visualization_url);
      }

      // 결과를 localStorage에 저장
      saveAnalysisResult(analysisId, {
        filename: resultData.filename,
        engine: resultData.engine,
        extracted_text: resultData.extracted_text,
        word_count: resultData.word_count,
        confidence_score: resultData.confidence_score,
        processing_time: resultData.processing_time,
        visualization_url: resultData.visualization_url,
        timestamp: resultData.timestamp,
        status: "completed",
      });

      console.log("✅ 분석 결과 조회 성공 및 저장 완료");
    } catch (error) {
      console.error("❌ 결과 조회 실패:", error);
      setOcrResult(`❌ 결과 조회 실패: ${error.message}`);
    }
  };

  const startPolling = (analysisId) => {
    pollingIntervalRef.current = setInterval(() => {
      checkAnalysisStatus(analysisId);
    }, 3000); // 3초마다 상태 확인 (더 자주)
  };

  const handleProcessAsync = async () => {
    if (!selectedFile) return;

    setIsProcessing(true);
    setOcrResult("");
    setVisualizationUrl(null);
    setShowVisualization(false);
    setProgressPercentage(0);
    setCurrentStep("분석 시작 중");

    try {
      const formData = new FormData();
      formData.append("file", selectedFile);

      const engine = selectedModel === "ppocr" ? "paddle" : "azure";
      formData.append("engine", engine);
      formData.append("extract_text_only", "false");
      formData.append("visualization", "true");

      console.log("🚀 비동기식 OCR 요청:", { engine, fileName: selectedFile.name });

      const response = await fetch("/api/ocr/analyze-async", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      const analysisId = data.analysis_id;

      setCurrentAnalysisId(analysisId);
      localStorage.setItem(STORAGE_KEYS.currentAnalysis, analysisId);

      console.log("✅ 비동기 분석 시작:", { analysisId, estimatedTime: data.estimated_time });

      // 폴링 시작
      startPolling(analysisId);
    } catch (error) {
      console.error("❌ 비동기 분석 요청 실패:", error);
      setIsProcessing(false);
      setOcrResult(`❌ ${error.message}`);
    }
  };

  const handleShowVisualization = () => {
    if (visualizationUrl) {
      setShowVisualization(true);
    } else if (currentAnalysisId && analysisResults[currentAnalysisId]?.visualization_url) {
      setVisualizationUrl(analysisResults[currentAnalysisId].visualization_url);
      setShowVisualization(true);
    } else {
      alert("분석 이미지를 찾을 수 없습니다. 분석을 다시 실행해주세요.");
    }
  };

  const renderAnalysisHistory = () => {
    const recentResults = Object.entries(analysisResults)
      .filter(([_, result]) => result.status === "completed")
      .sort(([_, a], [__, b]) => new Date(b.timestamp) - new Date(a.timestamp))
      .slice(0, 5);

    if (recentResults.length === 0) return null;

    return (
      <div className="analysis-history">
        <h4>최근 분석 결과</h4>
        <div className="history-list">
          {recentResults.map(([id, result]) => (
            <div key={id} className="history-item">
              <div className="history-info">
                <span className="filename">{result.filename}</span>
                <span className="timestamp">{new Date(result.timestamp).toLocaleString()}</span>
              </div>
              <button
                className="btn btn-sm"
                onClick={() => {
                  setOcrResult(result.extracted_text);
                  setVisualizationUrl(result.visualization_url);
                  setCurrentAnalysisId(id);
                }}>
                불러오기
              </button>
            </div>
          ))}
        </div>
      </div>
    );
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

      {renderAnalysisHistory()}

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
                  <span className="model-desc">한문 및 고문서 특화 모델 (1-2분 소요)</span>
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
                  <span className="model-desc">범용 문서 인식 모델 (30-60초 소요)</span>
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
              onClick={handleProcessAsync}
              disabled={!selectedFile || isProcessing}>
              {isProcessing ? (
                <>
                  <div className="spinner" />
                  분석 중...
                </>
              ) : (
                <>
                  <Play size={16} />
                  OCR 분석 실행
                </>
              )}
            </button>
          </div>
        </div>

        {/* 진행률 표시 */}
        {isProcessing && (
          <div className="progress-container">
            <div className="progress-info">
              <span className="progress-text">{currentStep || "분석 중..."}</span>
              <span className="progress-percentage">{progressPercentage}%</span>
            </div>
            <div className="progress-bar">
              <div className="progress-fill" style={{ width: `${progressPercentage}%` }} />
            </div>
            <div className="progress-details">
              <Clock size={16} />
              <span>백그라운드에서 분석 중... 다른 페이지로 이동해도 계속 처리됩니다.</span>
            </div>
          </div>
        )}

        {/* 분석 ID 표시 */}
        {currentAnalysisId && (
          <div className="analysis-info">
            <p>
              분석 ID: <code>{currentAnalysisId.substring(0, 8)}...</code>
            </p>
          </div>
        )}

        {/* 메인 콘텐츠 영역 */}
        <div className="ocr-content">
          <div className="content-grid">
            {/* 왼쪽: 원본 이미지 */}
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
                    <FileImage size={35} />
                    <p>이미지를 드래그하거나 클릭하여 업로드하세요.</p>
                    <p className="upload-hint">지원 형식: JPG, PNG, GIF (최대 10MB)</p>
                  </div>
                )}
              </div>
            </div>

            {/* 오른쪽: 분석 결과 */}
            <div className="result-section">
              <h3>
                <Focus size={20} />
                분석 결과
              </h3>
              <div className="result-area">
                {ocrResult ? (
                  <div className="result-content">
                    <div className="result-header">
                      <CheckCircle size={20} className="success-icon" />
                      <span>분석 완료</span>
                      {currentAnalysisId && (
                        <span className="analysis-id">ID: {currentAnalysisId.substring(0, 8)}</span>
                      )}
                    </div>

                    {/* 추출된 텍스트 */}
                    <div className="text-result">
                      <h4>추출된 텍스트</h4>
                      <div className="extracted-text-container">
                        <pre className="extracted-text">{ocrResult}</pre>
                      </div>
                    </div>

                    {/* 분석 이미지 표시 토글 */}
                    {showVisualization && visualizationUrl && (
                      <div className="visualization-section">
                        <h4>
                          <ImageIcon size={16} />
                          OCR 분석 시각화
                        </h4>
                        <div className="visualization-image">
                          <img
                            src={visualizationUrl}
                            alt="OCR 분석 결과 시각화"
                            onError={(e) => {
                              console.warn("시각화 이미지 로드 실패");
                              e.target.style.display = "none";
                            }}
                          />
                        </div>
                        <button
                          className="btn btn-secondary mt-2"
                          onClick={() => setShowVisualization(false)}>
                          이미지 숨기기
                        </button>
                      </div>
                    )}

                    <div className="result-actions">
                      <button
                        className="btn btn-secondary"
                        onClick={handleShowVisualization}
                        disabled={
                          !visualizationUrl &&
                          !(
                            currentAnalysisId &&
                            analysisResults[currentAnalysisId]?.visualization_url
                          )
                        }>
                        <Eye size={16} />
                        분석 이미지 표기
                      </button>
                      <button
                        className="btn btn-secondary"
                        onClick={() => {
                          navigator.clipboard.writeText(ocrResult);
                          alert("텍스트가 복사되었습니다.");
                        }}>
                        텍스트 복사
                      </button>
                      {visualizationUrl && (
                        <a
                          href={visualizationUrl}
                          download={`ocr_result_${
                            currentAnalysisId?.substring(0, 8) || "image"
                          }.jpg`}
                          className="btn btn-secondary">
                          시각화 이미지 다운로드
                        </a>
                      )}
                    </div>
                  </div>
                ) : (
                  <div className="result-placeholder">
                    {isProcessing ? (
                      <>
                        <div className="spinner large" />
                        <p>분석 진행 중입니다...</p>
                        <p className="sub-text">페이지를 떠나도 백그라운드에서 계속 처리됩니다</p>
                      </>
                    ) : (
                      <>
                        <AlertCircle size={24} />
                        <p>이미지를 업로드하고 분석을 실행하세요</p>
                      </>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default OcrPage;
