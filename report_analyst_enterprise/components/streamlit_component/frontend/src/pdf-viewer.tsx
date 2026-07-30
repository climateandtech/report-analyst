/**
 * PDF Viewer React component for Streamlit
 * 
 * Wraps the framework-agnostic web component for use in Streamlit.
 */

import React, { useEffect, useRef } from "react";
import { Streamlit } from "streamlit-component-lib";

interface PdfViewerProps {
  pdfUrl?: string;
  pdfData?: string;
  chunks: string; // JSON string
  questions: string; // JSON string
  selectedQuestionId?: string;
  showEvidenceOnly?: boolean;
}

// Extend HTMLElement to include web component methods
interface PdfViewerElement extends HTMLElement {
  setPdfUrl(url: string): void;
  setPdfData(data: string): void;
  setChunks(chunks: any[]): void;
  setQuestions(questions: any[]): void;
  setSelectedQuestionId(questionId: string | null): void;
  setShowEvidenceOnly(show: boolean): void;
  navigateToPage(pageNum: number): Promise<void>;
  navigateToChunk(chunk: any): Promise<void>;
  navigateToChunkById(chunkId: string): Promise<void>;
}

const PdfViewer: React.FC<PdfViewerProps> = (props) => {
  const viewerRef = useRef<PdfViewerElement | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const heightUpdateTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const lastHeightRef = useRef<number>(0);
  const observerRef = useRef<MutationObserver | null>(null);

  // Parse props
  const chunks = JSON.parse(props.chunks || "[]");
  const questions = JSON.parse(props.questions || "[]");

  // Debounced height update function
  const updateFrameHeight = React.useCallback(() => {
    if (heightUpdateTimeoutRef.current) {
      clearTimeout(heightUpdateTimeoutRef.current);
    }

    heightUpdateTimeoutRef.current = setTimeout(() => {
      try {
        const container = containerRef.current;
        if (!container) return;

        const height = Math.max(
          container.offsetHeight || container.scrollHeight || 800,
          800 // minimum height
        );

        if (Math.abs(height - lastHeightRef.current) > 50 || lastHeightRef.current === 0) {
          lastHeightRef.current = height;
          Streamlit.setFrameHeight(height);
        }
      } catch (e) {
        console.debug('Could not set frame height yet:', e);
      }
    }, 150);
  }, []);

  useEffect(() => {
    // Load web component script if not already loaded
    const loadWebComponent = async () => {
      // Check if web component is already defined
      if (customElements.get('pdf-viewer-with-chunks')) {
        createViewerElement();
        return;
      }

      // Load PDF.js first
      if (typeof window.pdfjsLib === 'undefined') {
        const pdfjsScript = document.createElement('script');
        pdfjsScript.src = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js';
        pdfjsScript.async = true;
        await new Promise((resolve, reject) => {
          pdfjsScript.onload = resolve;
          pdfjsScript.onerror = reject;
          document.head.appendChild(pdfjsScript);
        });
      }

      // Load the web component script
      const script = document.createElement('script');
      script.type = 'module';
      script.src = './pdf-viewer.es.js';
      
      const waitForCustomElement = (maxAttempts = 50) => {
        let attempts = 0;
        const check = () => {
          if (customElements.get('pdf-viewer-with-chunks')) {
            createViewerElement();
          } else if (attempts < maxAttempts) {
            attempts++;
            setTimeout(check, 100);
          } else {
            console.error('Custom element pdf-viewer-with-chunks not defined after loading script');
          }
        };
        setTimeout(check, 100);
      };
      
      script.onload = () => {
        waitForCustomElement();
      };
      script.onerror = (e) => {
        console.error('Failed to load web component from', script.src, e);
        // Try absolute path as fallback (for dev server)
        const fallbackScript = document.createElement('script');
        fallbackScript.type = 'module';
        fallbackScript.src = '/pdf-viewer.es.js';
        fallbackScript.onload = () => {
          waitForCustomElement();
        };
        fallbackScript.onerror = (e2) => {
          console.error('Failed to load web component from fallback path:', e2);
        };
        document.head.appendChild(fallbackScript);
      };
      document.head.appendChild(script);
    };

    const createViewerElement = () => {
      if (!containerRef.current) return;

      // Remove existing viewer if any
      const existing = containerRef.current.querySelector('pdf-viewer-with-chunks');
      if (existing) {
        existing.remove();
      }

      // Disconnect previous observer
      if (observerRef.current) {
        observerRef.current.disconnect();
        observerRef.current = null;
      }

      // Create web component element
      const viewerElement = document.createElement('pdf-viewer-with-chunks') as PdfViewerElement;
      viewerRef.current = viewerElement;

      // Set properties
      if (props.pdfUrl) {
        viewerElement.setPdfUrl(props.pdfUrl);
      } else if (props.pdfData) {
        viewerElement.setPdfData(props.pdfData);
      }
      viewerElement.setChunks(chunks);
      viewerElement.setQuestions(questions);
      if (props.selectedQuestionId) {
        viewerElement.setSelectedQuestionId(props.selectedQuestionId);
      }
      viewerElement.setShowEvidenceOnly(props.showEvidenceOnly || false);

      // Set up event listeners
      const handleChunkSelected = (e: CustomEvent) => {
        Streamlit.setComponentValue({
          type: "chunk-selected",
          chunk: e.detail.chunk,
          pageNum: e.detail.pageNum,
        });
        updateFrameHeight();
      };

      viewerElement.addEventListener('chunk-selected', handleChunkSelected as EventListener);

      // Append to container
      containerRef.current.appendChild(viewerElement);

      // Set up mutation observer for dynamic height updates
      observerRef.current = new MutationObserver(() => {
        updateFrameHeight();
      });

      if (containerRef.current) {
        observerRef.current.observe(containerRef.current, {
          childList: true,
          subtree: true,
          attributes: false
        });
      }

      // Initial height update
      setTimeout(updateFrameHeight, 500);
    };

    loadWebComponent();

    // Update when props change
    if (viewerRef.current) {
      if (props.pdfUrl) {
        viewerRef.current.setPdfUrl(props.pdfUrl);
      } else if (props.pdfData) {
        viewerRef.current.setPdfData(props.pdfData);
      }
      viewerRef.current.setChunks(chunks);
      viewerRef.current.setQuestions(questions);
      if (props.selectedQuestionId) {
        viewerRef.current.setSelectedQuestionId(props.selectedQuestionId);
      }
      viewerRef.current.setShowEvidenceOnly(props.showEvidenceOnly || false);
      updateFrameHeight();
    }

    return () => {
      // Cleanup
      if (heightUpdateTimeoutRef.current) {
        clearTimeout(heightUpdateTimeoutRef.current);
      }
      if (observerRef.current) {
        observerRef.current.disconnect();
        observerRef.current = null;
      }
      if (viewerRef.current) {
        viewerRef.current.remove();
        viewerRef.current = null;
      }
    };
  }, [props.pdfUrl, props.pdfData, props.chunks, props.questions, props.selectedQuestionId, props.showEvidenceOnly, chunks, questions, updateFrameHeight]);

  // Watch for highlightChunkId changes and navigate to chunk
  useEffect(() => {
    if (props.highlightChunkId && viewerRef.current) {
      viewerRef.current.navigateToChunkById(props.highlightChunkId);
      updateFrameHeight();
    }
  }, [props.highlightChunkId, updateFrameHeight]);

  return (
    <div 
      ref={containerRef}
      style={{ 
        width: "100%", 
        minHeight: "800px",
      }}
    />
  );
};

export default PdfViewer;

