import { defineConfig } from "vite"
import react from "@vitejs/plugin-react"
import path from "path"

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: path.resolve(__dirname, "dist/qr_scanner_component"),
    emptyOutDir: true,
    rollupOptions: {
      input: {
        main: path.resolve(__dirname, "index.html"),
      },
    },
  },
  base: "./", // ⚠️ importantísimo para que los assets se sirvan con rutas relativas
})
