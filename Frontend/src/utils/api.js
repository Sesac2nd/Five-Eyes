import axios from "axios";

// 환경변수에서 설정 읽기
const API_CONFIG = {
  BASE_URL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8001",
  TIMEOUT: parseInt(import.meta.env.VITE_API_TIMEOUT) || 15000,
  APP_ENV: import.meta.env.VITE_APP_ENV || "development",
};

console.log("🔧 Frontend API Configuration:", API_CONFIG);

const apiClient = axios.create({
  baseURL: API_CONFIG.BASE_URL,
  timeout: API_CONFIG.TIMEOUT,
  headers: {
    "Content-Type": "application/json",
  },
});

// 요청 인터셉터
apiClient.interceptors.request.use(
  (config) => {
    if (API_CONFIG.APP_ENV === "development") {
      console.log(`🚀 API Request: ${config.method?.toUpperCase()} ${config.url}`);
    }
    return config;
  },
  (error) => {
    console.error("❌ API Request Error:", error);
    return Promise.reject(error);
  }
);

// 응답 인터셉터
apiClient.interceptors.response.use(
  (response) => {
    if (API_CONFIG.APP_ENV === "development") {
      console.log(`✅ API Response: ${response.status} ${response.config.url}`);
    }
    return response;
  },
  (error) => {
    const { response, config } = error;
    if (response) {
      console.error(`❌ API Error: ${response.status} ${config?.url}`);
    } else {
      console.error(`❌ Network Error: ${config?.url}`, error.message);
    }
    return Promise.reject(error);
  }
);

export default apiClient;
