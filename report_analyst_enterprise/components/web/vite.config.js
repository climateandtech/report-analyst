import { defineConfig } from 'vite';

export default defineConfig({
  define: {
    'process.env': JSON.stringify({ NODE_ENV: 'production' }),
    process: JSON.stringify({ env: { NODE_ENV: 'production' } }),
  },
  build: {
    lib: {
      entry: {
        'pdf-viewer': 'src/pdf-viewer.js',
      },
      name: '[name]',
      fileName: (format, entryName) => `${entryName}.${format}.js`,
      formats: ['es'],
    },
    rollupOptions: {
      external: [],
      output: {
        globals: {},
      },
    },
  },
  server: {
    port: 3004,
    cors: true,
  },
});
