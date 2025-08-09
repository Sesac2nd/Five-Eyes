import axios from "axios";

// 환경 감지 함수
const getEnvironment = () => {
  // 현재 도메인 기준으로 환경 판단
  const hostname = window.location.hostname;
  
  if (hostname === "localhost" || hostname === "127.0.0.1") {
    return "development";
  } else if (hostname.includes("azurestaticapps.net")) {
    return "production";
  } else {
    return "development"; // 기본값
  }
};

// 환경별 API 설정
const getApiConfig = () => {
  const environment = getEnvironment();
  
  const configs = {
    development: {
      BASE_URL: "http://localhost:8001",
      TIMEOUT: 15000,
      APP_ENV: "development",
    },
    production: {
      BASE_URL: "https://5teamback.azurewebsites.net",
      TIMEOUT: 30000, // 프로덕션에서는 더 긴 타임아웃
      APP_ENV: "production",
    }
  };

  return configs[environment];
};

const API_CONFIG = getApiConfig();

console.log("🔧 Frontend API Configuration:", {
  environment: getEnvironment(),
  hostname: window.location.hostname,
  ...API_CONFIG
});

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
      console.log(`🚀 API Request: ${config.method?.toUpperCase()} ${config.baseURL}${config.url}`);
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
      console.error(`❌ API Error: ${response.status} ${config?.url}`, {
        status: response.status,
        statusText: response.statusText,
        data: response.data,
        url: `${config?.baseURL}${config?.url}`
      });
    } else {
      console.error(`❌ Network Error: ${config?.url}`, error.message);
    }
    return Promise.reject(error);
  }
);

// API 설정 정보를 외부에서 접근할 수 있도록 export
export { API_CONFIG };
export default apiClient;
