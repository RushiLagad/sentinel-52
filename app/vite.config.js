import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// base must match the GitHub Pages path for the repository, and the app uses
// hash routing so that a deep link survives a static host with no rewrites.
export default defineConfig({
  plugins: [react()],
  base: "/sentinel-52/",
  build: { outDir: "dist", sourcemap: false },
  test: { environment: "jsdom", globals: true, setupFiles: [] },
});
