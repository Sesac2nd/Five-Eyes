import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { resolve } from "path";

// https://vitejs.dev/config/
export default defineConfig({
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
});
