import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  define: {
    'process.env': JSON.stringify({ NODE_ENV: 'production' }),
    'process': JSON.stringify({ env: { NODE_ENV: 'production' } }),
  },
  build: {
    lib: {
      entry: {
        'json-schema-form': 'src/json-schema-form.js',
        'pdf-viewer': 'src/pdf-viewer.js',
      },
      name: '[name]',
      fileName: (format, entryName) => `${entryName}.${format}.js`,
      formats: ['es']
    },
    rollupOptions: {
      external: [], // Bundle everything for standalone use
      output: {
        // For multiple entry points, we can't use inlineDynamicImports
        // Each entry will be a separate bundle
        globals: {}
      }
    }
  },
  server: {
    port: 3004,
    cors: true
  }
});

