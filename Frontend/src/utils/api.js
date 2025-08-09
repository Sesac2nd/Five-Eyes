import axios from "axios";

// 런타임 환경 감지 함수
const getEnvironment = () => {
  const hostname = window.location.hostname;
  
  if (hostname === "localhost" || hostname === "127.0.0.1") {
    return "development";
  } else if (hostname.includes("azurestaticapps.net")) {
    return "production";
  } else {
    return "development";
  }
};

// 런타임 API 설정 (빌드 타임이 아닌 런타임에 결정)
const getApiConfig = () => {
  const environment = getEnvironment();
  const hostname = window.location.hostname;
  
  // 1순위: 런타임 환경변수 (Azure Static Web Apps에서 설정)
  const runtimeApiUrl = window._env_?.VITE_API_BASE_URL || 
                       window.ENV?.API_BASE_URL ||
                       process.env.REACT_APP_API_BASE_URL;
  
  // 2순위: Vite 빌드타임 환경변수
  const buildTimeApiUrl = import.meta.env?.VITE_API_BASE_URL;
  
  // 3순위: 도메인 기반 자동 감지
  const configs = {
    development: {
      BASE_URL: runtimeApiUrl || buildTimeApiUrl || "http://localhost:8001",
      TIMEOUT: 15000,
      APP_ENV: "development",
    },
    production: {
      BASE_URL: runtimeApiUrl || buildTimeApiUrl || "https://5teamback.azurewebsites.net",
      TIMEOUT: 30000,
      APP_ENV: "production",
    }
  };

  const config = configs[environment];
  
  // 로깅으로 어떤 방식으로 API URL이 결정되었는지 확인
  console.log("🔍 API URL 결정 과정:", {
    hostname,
    environment,
    runtimeApiUrl,
    buildTimeApiUrl,
    finalBaseUrl: config.BASE_URL,
    source: runtimeApiUrl ? "runtime" : buildTimeApiUrl ? "buildtime" : "default"
  });

  return config;
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
