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
  
  // 🔥 Azure Static Web Apps는 자체 도메인으로 API 프록시 사용
  const configs = {
    development: {
      BASE_URL: "http://localhost:8001",
      TIMEOUT: 15000,
      APP_ENV: "development",
    },
    production: {
      // 🔥 프로덕션에서는 현재 도메인의 /api로 요청 (staticwebapp.config.json이 프록시 처리)
      BASE_URL: "", // 빈 문자열로 하면 현재 도메인 사용
      TIMEOUT: 30000,
      APP_ENV: "production",
    }
  };

  const config = configs[environment];
  
  // 로깅으로 어떤 방식으로 API URL이 결정되었는지 확인
  console.log("🔍 API URL 결정 과정:", {
    hostname,
    environment,
    finalBaseUrl: config.BASE_URL || "현재 도메인 사용",
    fullApiPath: config.BASE_URL ? `${config.BASE_URL}/api` : `${window.location.origin}/api`,
    proxyEnabled: environment === "production"
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

// 🔥 요청 인터셉터 - 환경별 경로 처리
apiClient.interceptors.request.use(
  (config) => {
    const isDevelopment = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1";
    
    // 🔥 개발환경에서는 /api 경로가 이미 포함되어 있으므로 그대로 사용
    // 프로덕션에서는 staticwebapp.config.json이 /api/*를 백엔드로 프록시하므로 /api 경로 필요
    if (!isDevelopment && !config.url.startsWith("/api") && !config.url.startsWith("http")) {
      config.url = `/api${config.url}`;
    }
    
    if (API_CONFIG.APP_ENV === "development" || isDevelopment) {
      console.log(`🚀 API Request [${isDevelopment ? 'DEV' : 'PROD'}]: ${config.method?.toUpperCase()} ${config.baseURL}${config.url}`);
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
    
    // 🔥 405 에러 특별 처리
    if (response?.status === 405) {
      console.error(`❌ 405 Method Not Allowed:`, {
        url: `${config?.baseURL}${config?.url}`,
        method: config?.method?.toUpperCase(),
        allowedMethods: response.headers?.allow || "Unknown",
        message: "백엔드 엔드포인트 메서드를 확인하세요"
      });
    } else if (response) {
      console.error(`❌ API Error: ${response.status} ${config?.url}`, {
        status: response.status,
        statusText: response.statusText,
        data: response.data,
        url: `${config?.baseURL}${config?.url}`,
        method: config?.method?.toUpperCase()
      });
    } else {
      console.error(`❌ Network Error: ${config?.url}`, {
        message: error.message,
        url: `${config?.baseURL}${config?.url}`,
        method: config?.method?.toUpperCase()
      });
    }
    return Promise.reject(error);
  }
);

// API 설정 정보를 외부에서 접근할 수 있도록 export
export { API_CONFIG };
export default apiClient;
