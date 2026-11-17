import { defineConfig } from "vite";

// The keyboard app (max68he) listens on 127.0.0.1:6869 without CORS headers
// for this page, so the dev server and `vite preview` pass /kb/... through to
// it: same origin, no CORS. 127.0.0.1, not localhost: on Windows localhost
// tries IPv6 first and the app only listens on IPv4.
const keyboardApp = {
  "/kb": {
    target: "http://127.0.0.1:6869",
    changeOrigin: true,
    rewrite: (p) => p.replace(/^\/kb/, ""),
  },
};

export default defineConfig({
  base: "./",
  server: { port: 5178, strictPort: false, proxy: keyboardApp },
  preview: { port: 5179, proxy: keyboardApp },
  build: { target: "es2022", outDir: "dist" },
});
