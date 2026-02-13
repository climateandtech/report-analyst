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
        const webComponentPath = join(__dirname, '../../web/dist/pdf-viewer.es.js');
        const publicPath = join(__dirname, 'public/pdf-viewer.es.js');
        const buildPath = join(__dirname, 'build/pdf-viewer.es.js');
        
        // Copy to public for dev server
        if (existsSync(webComponentPath)) {
          try {
            copyFileSync(webComponentPath, publicPath);
            console.log('✓ Copied PDF viewer web component to public/');
          } catch (e) {
            console.warn('Could not copy PDF viewer web component to public:', e);
          }
        }
        
        // Copy to build for production
        if (existsSync(webComponentPath)) {
          try {
            copyFileSync(webComponentPath, buildPath);
            console.log('✓ Copied PDF viewer web component to build/');
          } catch (e) {
            console.warn('Could not copy PDF viewer web component to build:', e);
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
    emptyOutDir: false,  // Don't clean build directory to preserve JSON schema form files
    rollupOptions: {
      input: 'index-pdf-viewer.html',  // Use PDF viewer HTML as entry point
      output: {
        entryFileNames: 'index-pdf-viewer.js',
        format: 'es',
      },
    },
      // Copy pdf-viewer.es.js to build directory
      copyPublicDir: true,
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
    include: ['react', 'react-dom', 'streamlit-component-lib'],
    esbuildOptions: {
      target: 'es2020',
    },
  },
  server: {
    port: 3002,  // Different port from JSON schema form
    cors: true,
  },
  publicDir: 'public',
});

