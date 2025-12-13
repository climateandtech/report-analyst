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
      entry: 'src/json-schema-form.js',
      name: 'JsonSchemaForm',
      fileName: (format) => `json-schema-form.${format}.js`,
      formats: ['es']
    },
    rollupOptions: {
      external: [], // Bundle everything for standalone use
      output: {
        // Ensure single file output for web component
        inlineDynamicImports: true,
        globals: {}
      }
    }
  },
  server: {
    port: 3004,
    cors: true
  }
});

