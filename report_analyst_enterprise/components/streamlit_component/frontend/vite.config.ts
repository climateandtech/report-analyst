import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { copyFileSync, existsSync } from 'fs';
import { join } from 'path';

export default defineConfig({
  plugins: [
    react(),
    // Plugin to copy web component to build directory
    {
      name: 'copy-web-component',
      writeBundle() {
        const webComponentPath = join(__dirname, '../../web/dist/json-schema-form.es.js');
        const publicPath = join(__dirname, 'public/json-schema-form.es.js');
        const buildPath = join(__dirname, 'build/json-schema-form.es.js');
        
        // Copy to public for dev server
        if (existsSync(webComponentPath)) {
          try {
            copyFileSync(webComponentPath, publicPath);
            console.log('✓ Copied web component to public/');
          } catch (e) {
            console.warn('Could not copy web component to public:', e);
          }
        }
        
        // Copy to build for production
        if (existsSync(webComponentPath)) {
          try {
            copyFileSync(webComponentPath, buildPath);
            console.log('✓ Copied web component to build/');
          } catch (e) {
            console.warn('Could not copy web component to build:', e);
          }
        }
      },
    },
  ],
  define: {
    'process.env': '{}',
    'process': JSON.stringify({ env: {} }),
  },
  build: {
    outDir: 'build',
    rollupOptions: {
      input: 'index.html',  // Use HTML as entry point - Vite will handle it
      output: {
        entryFileNames: 'index.js',
        format: 'es',
      },
    },
    // Ensure relative paths in HTML
    base: './',
    commonjsOptions: {
      include: [/node_modules/],
      transformMixedEsModules: true,
      strictRequires: true,
    },
    target: 'es2020',
  },
  optimizeDeps: {
    include: ['@rjsf/utils', '@rjsf/validator-ajv8', '@rjsf/core', '@rjsf/mui', '@mui/material', '@emotion/react', '@emotion/styled'],
    esbuildOptions: {
      target: 'es2020',
    },
  },
  server: {
    port: 3001,
    cors: true,
  },
  publicDir: 'public',
});

