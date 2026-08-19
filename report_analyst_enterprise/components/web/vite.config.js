import { defineConfig } from "vite";
import { copyFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

const outputDirectory = fileURLToPath(
  new URL("../streamlit_component/frontend/public", import.meta.url),
);

export default defineConfig({
  plugins: [
    {
      name: "copy-pdf-worker",
      writeBundle() {
        copyFileSync(
          fileURLToPath(
            new URL("./node_modules/pdfjs-dist/build/pdf.worker.min.mjs", import.meta.url),
          ),
          `${outputDirectory}/pdf.worker.min.mjs`,
        );
      },
    },
  ],
  build: {
    emptyOutDir: false,
    lib: {
      entry: "src/pdf-viewer.js",
      formats: ["es"],
      fileName: () => "pdf-viewer.es.js",
    },
    outDir: outputDirectory,
  },
});
