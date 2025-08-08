import { defineConfig, loadEnv } from "vite";
import svgr from "vite-plugin-svgr";
import react from "@vitejs/plugin-react";
import { resolve } from "path";

export default defineConfig(({ mode }) => {
  // 환경변수 로드 (VITE_ 접두사가 있는 변수들)
  const env = loadEnv(mode, process.cwd(), "VITE_");

  // API Base URL 결정
  const apiBaseUrl = env.VITE_API_BASE_URL || "http://localhost:8001";

  console.log(`🚀 Mode: ${mode}`);
  console.log(`🔗 API Base URL: ${apiBaseUrl}`);

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
      proxy: {
        "/api": {
          target: apiBaseUrl,
          changeOrigin: true,
          secure: isHttps, // HTTPS일 때만 보안 검증
          ws: true, // WebSocket 지원
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
            timeout: 30000,
            proxyTimeout: 30000,
          }),
        },
      },
    },
    build: {
      outDir: "dist",
      sourcemap: false,
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
      __APP_ENV__: JSON.stringify(env.VITE_APP_ENV || "development"),
    },
  };
});
