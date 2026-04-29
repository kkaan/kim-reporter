import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "node:path";

// Build the React bundle into kim_app/web_dist/ so the Python package can
// serve it directly (and PyInstaller can pick it up via package_data).
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "src"),
    },
  },
  server: {
    port: 5173,
    strictPort: false,
    // Forward /api/* to the Python backend so `http://localhost:5173` works
    // in a browser without needing the ?api=... query param that pywebview
    // injects. The default backend port (8765) matches _free_port() in
    // kim_app/__main__.py; start the backend with `python -m kim_app` first.
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8765",
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: path.resolve(__dirname, "../kim_app/web_dist"),
    emptyOutDir: true,
    sourcemap: false,
    chunkSizeWarningLimit: 1500,
  },
});
