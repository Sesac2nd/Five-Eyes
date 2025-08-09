// Frontend/src/pages/OcrPage.jsx
import { useState, useEffect } from "react";
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

  // 비동기 OCR 처리를 위한 개선된 handleProcess 함수

  // 기존 /api/ocr/analyze 엔드포인트를 사용하되 연결 안정성을 강화한 handleProcess

  const handleProcess = async () => {
    if (!selectedFile) return;

    setIsProcessing(true);

    try {
      const formData = new FormData();
      formData.append("file", selectedFile);

      const engine = selectedModel === "ppocr" ? "paddle" : "azure";
      formData.append("engine", engine);
      formData.append("extract_text_only", "false");
      formData.append("visualization", "true");

      console.log("🚀 OCR 요청 시작:", {
        fileName: selectedFile.name,
        fileSize: selectedFile.size,
        engine: engine,
        selectedModel: selectedModel,
      });

      // 1. PaddleOCR 대기시간 안내
      if (engine === "paddle") {
        console.log("⏳ PaddleOCR 모드: 평균 1-2분 대기 예상");
        console.log("🔄 한문 특화 모델 로딩 및 분석 진행중...");
      }

      // 2. 요청 전 상태 로깅 및 진행 타이머 시작
      const requestStart = Date.now();
      let progressTimer;

      // 3. 진행상황 로깅 타이머 (15초마다)
      const logProgress = () => {
        const elapsed = Math.floor((Date.now() - requestStart) / 1000);
        const minutes = Math.floor(elapsed / 60);
        const seconds = elapsed % 60;

        if (engine === "paddle") {
          console.log(`⏱️ PaddleOCR 진행중... ${minutes}분 ${seconds}초 경과`);
          if (elapsed < 180) {
            // 3분까지만 로깅
            progressTimer = setTimeout(logProgress, 15000);
          }
        } else {
          console.log(`⏱️ Azure OCR 진행중... ${elapsed}초 경과`);
          if (elapsed < 60) {
            // 1분까지만 로깅
            progressTimer = setTimeout(logProgress, 10000);
          }
        }
      };

      // 4. 첫 진행상황 로깅 (15초 후 시작)
      progressTimer = setTimeout(logProgress, 15000);

      // 5. Fetch 요청 - 긴 타임아웃 설정 및 연결 안정성 강화
      const timeoutMs = engine === "paddle" ? 300000 : 90000; // Paddle: 5분, Azure: 1분30초 (타임아웃 증가)

      const controller = new AbortController();
      const timeoutId = setTimeout(() => {
        controller.abort();
        console.log(`❌ ${engine} OCR 요청 타임아웃 (${timeoutMs / 1000}초)`);
      }, timeoutMs);

      // 재시도 로직 추가
      let retryCount = 0;
      const maxRetries = 2;

      const attemptRequest = async () => {
        try {
          console.log(`📡 요청 시도 ${retryCount + 1}/${maxRetries + 1}`);

          const res = await fetch("/api/ocr/analyze", {
            method: "POST",
            body: formData,
            signal: controller.signal,
            // HTTP 연결 안정성 강화
            keepalive: true,
            // 추가 헤더로 연결 유지 요청
            headers: {
              Connection: "keep-alive",
              "Cache-Control": "no-cache",
            },
          });

          return res;
        } catch (fetchError) {
          console.warn(`⚠️ 요청 시도 ${retryCount + 1} 실패:`, fetchError.message);

          // 네트워크 에러이고 재시도 가능한 경우
          if (
            retryCount < maxRetries &&
            (fetchError.message.includes("ERR_CONNECTION") ||
              fetchError.message.includes("network") ||
              fetchError.name === "TypeError")
          ) {
            retryCount++;
            console.log(`🔄 ${retryCount}초 후 재시도...`);

            // 재시도 전 잠시 대기
            await new Promise((resolve) => setTimeout(resolve, retryCount * 1000));
            return attemptRequest();
          }

          // 재시도 불가능하거나 한도 초과
          throw fetchError;
        }
      };

      const res = await attemptRequest();

      // 6. 타이머 정리
      clearTimeout(timeoutId);
      clearTimeout(progressTimer);

      const requestEnd = Date.now();
      const totalTime = requestEnd - requestStart;
      const totalMinutes = Math.floor(totalTime / 60000);
      const totalSeconds = Math.floor((totalTime % 60000) / 1000);

      // 7. 응답 상태 상세 로깅
      console.log("📡 응답 상태:", {
        status: res.status,
        statusText: res.statusText,
        ok: res.ok,
        headers: Object.fromEntries(res.headers.entries()),
        totalProcessingTime: `${totalMinutes}분 ${totalSeconds}초 (${totalTime}ms)`,
        engine: engine,
        retryCount: retryCount,
      });

      // 8. 처리시간 분석
      if (engine === "paddle") {
        if (totalTime > 120000) {
          // 2분 이상
          console.log("🐌 PaddleOCR 처리시간이 예상보다 길었습니다 (2분+)");
        } else if (totalTime > 60000) {
          // 1분 이상
          console.log("⏱️ PaddleOCR 정상 처리시간 범위 (1-2분)");
        } else {
          console.log("⚡ PaddleOCR 빠른 처리 완료 (1분 미만)");
        }
      }

      // 9. 응답 처리 개선
      if (!res.ok) {
        let errorMessage;
        let errorDetails = {};

        try {
          // Content-Type 확인 후 적절한 파싱
          const contentType = res.headers.get("content-type");

          if (contentType && contentType.includes("application/json")) {
            const errorData = await res.json();
            errorMessage = errorData.detail || errorData.message || "알 수 없는 오류";
            errorDetails = errorData;
          } else {
            errorMessage = await res.text();
          }
        } catch (parseError) {
          console.error("❌ 응답 파싱 실패:", parseError);
          errorMessage = `HTTP ${res.status}: ${res.statusText}`;
        }

        console.error("❌ OCR 요청 실패:", {
          status: res.status,
          message: errorMessage,
          details: errorDetails,
        });

        throw new Error(`OCR 분석 실패 (${res.status}): ${errorMessage}`);
      }

      // 10. 성공 응답 처리
      const contentType = res.headers.get("content-type");
      if (!contentType || !contentType.includes("application/json")) {
        throw new Error(`잘못된 응답 형식: ${contentType}`);
      }

      const data = await res.json();

      // 11. 응답 데이터 검증
      console.log("✅ OCR 분석 성공:", {
        analysisId: data.analysis_id,
        status: data.status,
        textLength: data.extracted_text?.length || 0,
        confidence: data.confidence_score,
        processingTime: data.processing_time,
        wordCount: data.word_count,
        retryCount: retryCount,
      });

      // 12. 응답 데이터 유효성 검사
      if (!data.extracted_text && data.status === "success") {
        console.warn("⚠️ 텍스트 추출 결과가 비어있습니다");
        setOcrResult("분석은 완료되었으나 추출된 텍스트가 없습니다.");
      } else if (data.extracted_text) {
        setOcrResult(data.extracted_text);
      } else {
        throw new Error(`분석 상태: ${data.status || "unknown"}`);
      }

      // 13. 추가 정보 표시 (옵션)
      if (data.confidence_score) {
        console.log(`📊 신뢰도: ${(data.confidence_score * 100).toFixed(1)}%`);
      }
    } catch (error) {
      console.error("💥 OCR 처리 중 예외 발생:", error);

      // 타이머 정리 (에러 시에도)
      if (typeof progressTimer !== "undefined") {
        clearTimeout(progressTimer);
      }

      // 사용자 친화적 오류 메시지
      let userMessage;
      if (error.name === "AbortError") {
        const engineName = selectedModel === "ppocr" ? "PaddleOCR" : "Azure OCR";
        const expectedTime = selectedModel === "ppocr" ? "5분" : "1분30초";
        userMessage = `${engineName} 분석이 ${expectedTime} 내에 완료되지 않아 중단되었습니다. 이미지 크기를 줄이거나 다시 시도해주세요.`;
        console.log(`⏰ ${engineName} 타임아웃 발생 - 예상 처리시간을 초과했습니다.`);
      } else if (
        error.name === "TypeError" &&
        (error.message.includes("fetch") || error.message.includes("network"))
      ) {
        userMessage =
          "서버와의 네트워크 연결이 불안정합니다. 백엔드에서는 분석이 계속 진행 중일 수 있습니다.";
        console.log("🔄 재시도하거나 잠시 후 분석 기록을 확인해보세요.");

        // 네트워크 에러 시 추가 안내
        if (selectedModel === "ppocr") {
          console.log("💡 PaddleOCR은 처리시간이 길어 네트워크 연결이 끊어질 수 있습니다.");
          console.log("📝 해결방법: 1) 이미지 크기 축소, 2) 잠시 후 재시도, 3) Azure 모델 사용");
        }
      } else if (error.message.includes("파일만 지원")) {
        userMessage = "지원되지 않는 파일 형식입니다. 이미지 파일을 업로드해주세요.";
      } else {
        userMessage = error.message || "분석 중 알 수 없는 오류가 발생했습니다.";

        // 연결 관련 에러인지 추가 확인
        if (error.message.includes("ERR_CONNECTION") || error.message.includes("connection")) {
          userMessage +=
            "\n💡 백엔드 분석은 계속 진행 중일 수 있습니다. 잠시 후 분석 기록을 확인해보세요.";
        }
      }

      setOcrResult(`❌ ${userMessage}`);
    } finally {
      setIsProcessing(false);
    }
  };
  // UI에서 사용할 때
  // <button onClick={handleProcessAsync}>비동기 분석 실행</button>

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
                  <FileImage size={35} />
                  <p>이미지를 드래그하거나 클릭하여 업로드하세요.</p>
                  <p className="upload-hint">지원 형식: JPG, PNG, GIF (최대 10MB)</p>
                </div>
              )}
            </div>
          </div>

          <div className="result-section">
            <h3>
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
