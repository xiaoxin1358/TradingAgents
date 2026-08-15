import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      // Dev: forward API calls to the FastAPI backend (docs 3).
      "/api": "http://127.0.0.1:8000",
    },
  },
});
