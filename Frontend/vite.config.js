import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
import { resolve } from "path";

export default defineConfig(({ mode }) => {
  // 환경변수 로드
  const env = loadEnv(mode, process.cwd(), "VITE_");

  // 환경별 API Base URL 설정
  const getApiBaseUrl = (mode, env) => {
    // 1. 환경변수가 설정되어 있으면 우선 사용
    if (env.VITE_API_BASE_URL) {
      return env.VITE_API_BASE_URL;
    }

    // 2. mode에 따른 기본 설정
    switch (mode) {
      case "development":
        return "http://localhost:8001";
      case "production":
        return "https://5teamback.azurewebsites.net";

      default:
        return "http://localhost:8001";
    }
  };

  const apiBaseUrl = getApiBaseUrl(mode, env);

  console.log(`🚀 Vite Build Configuration:`);
  console.log(`   Mode: ${mode}`);
  console.log(`   API Base URL: ${apiBaseUrl}`);
  console.log(`   Environment: ${env.VITE_APP_ENV || mode}`);

  // URL이 https인지 http인지 확인
  const isHttps = apiBaseUrl.startsWith("https://");
  const isLocal = apiBaseUrl.includes("localhost") || apiBaseUrl.includes("127.0.0.1");

  return {
    publicDir: resolve(process.cwd(), "public"),
    resolve: {
      alias: {
        "@": resolve(process.cwd(), "src"),
      },
    },
    server: {
      host: "localhost",
      port: 3000,
      open: true,
      cors: true,
      // 개발 환경에서만 프록시 설정
      ...(mode === "development" && {
        proxy: {
          "/api": {
            target: apiBaseUrl,
            changeOrigin: true,
            secure: isHttps,
            ws: true,
            configure: (proxy, _options) => {
              console.log(`📡 Proxy configured: /api -> ${apiBaseUrl}`);

              proxy.on("error", (err, req, res) => {
                console.error("❌ Proxy error:", err.message);
                console.error(`Request: ${req.method} ${req.url}`);
              });

              proxy.on("proxyReq", (proxyReq, req, _res) => {
                console.log(`➡️  Proxying: ${req.method} ${req.url} -> ${apiBaseUrl}${req.url}`);
              });

              proxy.on("proxyRes", (proxyRes, req, _res) => {
                const status = proxyRes.statusCode;
                const statusIcon = status >= 200 && status < 300 ? "✅" : "❌";
                console.log(`⬅️  ${statusIcon} Response: ${status} ${req.url}`);
              });
            },
            // 로컬 개발 시 추가 설정
            ...(isLocal && {
              timeout: 300000,
              proxyTimeout: 300000,
            }),
          },
        },
      }),
    },
    build: {
      outDir: "dist",
      sourcemap: mode === "development", // 개발 환경에서만 소스맵 생성
      chunkSizeWarningLimit: 500,
      rollupOptions: {
        input: {
          main: resolve(process.cwd(), "index.html"),
        },
        output: {
          manualChunks: {
            vendor: ["react", "react-dom"],
            router: ["react-router-dom"],
            "lucide-react": ["lucide-react"],
          },
        },
      },
    },
    plugins: [react()],
    // 환경변수를 빌드 시에도 사용할 수 있도록
    define: {
      __API_BASE_URL__: JSON.stringify(apiBaseUrl),
      __APP_ENV__: JSON.stringify(env.VITE_APP_ENV || mode),
      __BUILD_MODE__: JSON.stringify(mode),
    },
    // 환경별 최적화 설정
    ...(mode === "production" && {
      build: {
        ...this?.build,
        minify: "terser",
        terserOptions: {
          compress: {
            drop_console: true, // 프로덕션에서 console.log 제거
            drop_debugger: true,
          },
        },
      },
    }),
  };
});
