/**
 * PDF Viewer with Chunks Web Component
 * 
 * Framework-agnostic web component that displays PDFs with chunk annotations.
 * Works in:
 * - Plain HTML/Vanilla JS
 * - React
 * - Svelte
 * - Streamlit (via iframe)
 * 
 * Uses PDF.js for PDF rendering.
 */

class PdfViewerWithChunks extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this._pdfUrl = null;
    this._pdfData = null;
    this._chunks = [];
    this._questions = [];
    this._selectedQuestionId = null;
    this._showEvidenceOnly = false;
    this._pdfDoc = null;
    this._currentPage = 1;
    this._scale = 1.5;
    this._pdfjsLib = null;
    this._renderedPages = new Map();
    this._isLoading = false;
    this._highlightedChunkId = null; // For tracking which chunk should be highlighted
  }

  static get observedAttributes() {
    return ['pdf-url', 'pdf-data', 'chunks', 'questions', 'selected-question-id', 'show-evidence-only'];
  }

  connectedCallback() {
    this.loadPdfJs().then(() => {
      this.render();
    });
  }

  disconnectedCallback() {
    // Cleanup
    this._renderedPages.clear();
    if (this._pdfDoc) {
      this._pdfDoc.destroy();
      this._pdfDoc = null;
    }
  }

  attributeChangedCallback(name, oldValue, newValue) {
    if (oldValue !== newValue) {
      try {
        if (name === 'pdf-url') {
          this._pdfUrl = newValue;
          this._pdfData = null;
        } else if (name === 'pdf-data') {
          this._pdfData = newValue;
          this._pdfUrl = null;
        } else if (name === 'chunks') {
          this._chunks = newValue ? JSON.parse(newValue) : [];
        } else if (name === 'questions') {
          this._questions = newValue ? JSON.parse(newValue) : [];
        } else if (name === 'selected-question-id') {
          this._selectedQuestionId = newValue;
        } else if (name === 'show-evidence-only') {
          this._showEvidenceOnly = newValue === 'true' || newValue === '';
        }
        
        // Only render if not skipping (i.e., external attribute change)
        // Internal state changes should update UI without full re-render
        if (!this._skipAttributeRender) {
          this.render();
        }
      } catch (e) {
        console.error(`Error parsing ${name}:`, e);
      }
    }
  }

  // Public API: Set PDF URL
  setPdfUrl(url) {
    this._pdfUrl = url;
    this._pdfData = null;
    this.setAttribute('pdf-url', url);
  }

  // Public API: Set PDF data (base64)
  setPdfData(data) {
    this._pdfData = data;
    this._pdfUrl = null;
    this.setAttribute('pdf-data', data);
  }

  // Public API: Set chunks
  setChunks(chunks) {
    this._chunks = chunks;
    this.setAttribute('chunks', JSON.stringify(chunks));
  }

  // Public API: Set questions
  setQuestions(questions) {
    this._questions = questions;
    this.setAttribute('questions', JSON.stringify(questions));
  }

  // Public API: Set selected question
  setSelectedQuestionId(questionId, skipRender = false) {
    this._selectedQuestionId = questionId;
    if (skipRender) {
      this._skipAttributeRender = true;
      this.setAttribute('selected-question-id', questionId || '');
      this._skipAttributeRender = false;
      // Update UI without full render
      this.updateFilterUI();
    } else {
      this.setAttribute('selected-question-id', questionId || '');
    }
  }

  // Public API: Set evidence filter
  setShowEvidenceOnly(show, skipRender = false) {
    this._showEvidenceOnly = show;
    if (skipRender) {
      this._skipAttributeRender = true;
      this.setAttribute('show-evidence-only', show ? 'true' : 'false');
      this._skipAttributeRender = false;
      // Update UI without full render
      this.updateFilterUI();
    } else {
      this.setAttribute('show-evidence-only', show ? 'true' : 'false');
    }
  }
  
  // Update filter UI without full render
  updateFilterUI() {
    const questionSelect = this.shadowRoot?.getElementById('question-select');
    if (questionSelect) {
      questionSelect.value = this._selectedQuestionId || '';
    }
    const evidenceFilter = this.shadowRoot?.getElementById('evidence-filter');
    if (evidenceFilter) {
      evidenceFilter.checked = this._showEvidenceOnly;
    }
    // Re-render chunk list only (not full PDF)
    this.renderChunkList();
  }
  
  // Render only the chunk list without re-rendering PDF
  renderChunkList() {
    const chunksList = this.shadowRoot?.querySelector('.chunks-list');
    if (!chunksList) return;
    
    const filteredChunks = this.getFilteredChunks();
    
    chunksList.innerHTML = filteredChunks.length === 0 
      ? '<div style="padding: 16px; color: #999; text-align: center;">No chunks to display</div>'
      : filteredChunks.map((chunk, idx) => {
          let pageNum = '?';
          if (chunk.metadata) {
            if (chunk.metadata.page_number !== undefined) {
              pageNum = parseInt(chunk.metadata.page_number) || '?';
            } else if (chunk.metadata.source !== undefined) {
              pageNum = parseInt(chunk.metadata.source) || '?';
            }
          }
          
          const isEvidence = chunk.is_evidence === true;
          const similarityScore = chunk.similarity_score?.toFixed(3) || 'N/A';
          const llmScore = chunk.llm_score?.toFixed(3) || 'N/A';
          const chunkText = chunk.text || '';
          const preview = chunkText.substring(0, 150) + (chunkText.length > 150 ? '...' : '');
          
          return `
            <div class="chunk-item ${isEvidence ? 'evidence' : ''}" data-chunk-index="${idx}">
              <div class="chunk-header">
                <span class="chunk-title">Chunk ${chunk.chunk_order !== undefined ? chunk.chunk_order + 1 : idx + 1}</span>
                <div style="display: flex; gap: 4px;">
                  ${isEvidence ? `<span class="chunk-badge evidence">Evidence</span>` : ''}
                  <span class="chunk-badge page">Page ${pageNum}</span>
                </div>
              </div>
              <div class="chunk-text">${this.escapeHtml(preview)}</div>
              <div class="chunk-scores">
                <span>Similarity: ${similarityScore}</span>
                ${chunk.llm_score !== null && chunk.llm_score !== undefined ? `<span>LLM: ${llmScore}</span>` : ''}
              </div>
            </div>
          `;
        }).join('');
    
    // Re-attach event listeners to chunk items
    this.attachChunkListeners();
  }
  
  // Attach click listeners to chunk items
  attachChunkListeners() {
    const chunkItems = this.shadowRoot?.querySelectorAll('.chunk-item');
    if (!chunkItems) return;
    
    chunkItems.forEach(item => {
      // Remove existing listeners by cloning
      const newItem = item.cloneNode(true);
      item.parentNode?.replaceChild(newItem, item);
      
      // Add new listener
      newItem.addEventListener('click', () => {
        const idx = parseInt(newItem.dataset.chunkIndex);
        const chunk = this.getFilteredChunks()[idx];
        if (chunk) {
          this.navigateToChunk(chunk);
        }
      });
    });
  }

  async loadPdfJs() {
    if (this._pdfjsLib) {
      return;
    }

    // Try to load PDF.js from CDN
    if (typeof pdfjsLib === 'undefined') {
      const script = document.createElement('script');
      script.src = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js';
      script.async = true;
      await new Promise((resolve, reject) => {
        script.onload = resolve;
        script.onerror = reject;
        document.head.appendChild(script);
      });
    }
    this._pdfjsLib = window.pdfjsLib || pdfjsLib;
    
    // Configure worker
    if (this._pdfjsLib.GlobalWorkerOptions) {
      this._pdfjsLib.GlobalWorkerOptions.workerSrc = 
        'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
    }
    
    // Configure CMap for proper font rendering (fixes font loading warnings)
    if (this._pdfjsLib.GlobalWorkerOptions) {
      this._pdfjsLib.GlobalWorkerOptions.cMapUrl = 
        'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/cmaps/';
      this._pdfjsLib.GlobalWorkerOptions.cMapPacked = true;
    }
  }

  async loadPdf() {
    if (!this._pdfjsLib) {
      await this.loadPdfJs();
    }

    if (this._pdfDoc) {
      return this._pdfDoc;
    }

    // Set loading state
    this._isLoading = true;
    this.updateLoadingDisplay();

    try {
      let loadingTask;
      // PDF.js options with CMap configuration
      const pdfOptions = {
        cMapUrl: 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/cmaps/',
        cMapPacked: true,
        standardFontDataUrl: 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/standard_fonts/',
      };
      
      if (this._pdfData) {
        // Base64 data
        const base64Data = this._pdfData.replace(/^data:application\/pdf;base64,/, '');
        const binaryString = atob(base64Data);
        const bytes = new Uint8Array(binaryString.length);
        for (let i = 0; i < binaryString.length; i++) {
          bytes[i] = binaryString.charCodeAt(i);
        }
        loadingTask = this._pdfjsLib.getDocument({ 
          data: bytes,
          ...pdfOptions
        });
      } else if (this._pdfUrl) {
        loadingTask = this._pdfjsLib.getDocument({
          url: this._pdfUrl,
          ...pdfOptions
        });
      } else {
        throw new Error('No PDF URL or data provided');
      }

      this._pdfDoc = await loadingTask.promise;
      return this._pdfDoc;
    } catch (error) {
      console.error('Error loading PDF:', error);
      throw error;
    }
  }

  updateLoadingDisplay() {
    const viewerContent = this.shadowRoot?.getElementById('viewer-content');
    if (!viewerContent) return;
    
    if (this._isLoading) {
      viewerContent.innerHTML = `
        <div class="loading">
          <div class="spinner"></div>
          <div class="loading-text">Loading PDF...</div>
        </div>
      `;
    }
    // If not loading, the content will be set by renderCurrentPage()
  }

  getFilteredChunks() {
    let chunks = [];
    
    if (this._selectedQuestionId) {
      // Get chunks for selected question
      const question = this._questions.find(q => q.question_id === this._selectedQuestionId);
      if (question && question.chunks) {
        chunks = question.chunks;
      } else {
        // Fallback: filter chunks by question_id in chunks array
        chunks = this._chunks.filter(c => c.question_id === this._selectedQuestionId);
      }
    } else {
      chunks = this._chunks;
    }

    // Apply evidence filter
    if (this._showEvidenceOnly) {
      chunks = chunks.filter(c => {
        // Handle both boolean (true/false) and integer (1/0) values from SQLite
        const isEvidence = c.is_evidence === true || c.is_evidence === 1;
        return isEvidence;
      });
    }

    return chunks;
  }

  async renderPage(pageNum) {
    if (this._renderedPages.has(pageNum)) {
      return this._renderedPages.get(pageNum);
    }

    try {
      const pdfDoc = await this.loadPdf();
      const page = await pdfDoc.getPage(pageNum);
      const viewport = page.getViewport({ scale: this._scale });

      const canvas = document.createElement('canvas');
      const context = canvas.getContext('2d');
      canvas.height = viewport.height;
      canvas.width = viewport.width;

      await page.render({
        canvasContext: context,
        viewport: viewport
      }).promise;

      this._renderedPages.set(pageNum, canvas);
      return canvas;
    } catch (error) {
      console.error(`Error rendering page ${pageNum}:`, error);
      return null;
    }
  }

  /**
   * Calculate log-likelihood keyness scores for words
   * Identifies words that are unusually frequent in this chunk compared to other chunks
   * Uses Dunning's log-likelihood (G²) statistic
   * @param {string} chunkText - The chunk text to analyze
   * @param {Array} allChunks - All chunk texts for comparison
   * @returns {Map<string, number>} Map of word to keyness score
   */
  calculateKeyness(chunkText, allChunks = []) {
    // Tokenize: split into words, lowercase, remove punctuation
    const tokenize = (str) => {
      return str.toLowerCase()
        .replace(/[^\w\s]/g, ' ')
        .split(/\s+/)
        .filter(word => word.length > 2); // Filter out very short words
    };
    
    // Tokenize the target chunk
    const chunkWords = tokenize(chunkText);
    const chunkWordCounts = new Map();
    chunkWords.forEach(word => {
      chunkWordCounts.set(word, (chunkWordCounts.get(word) || 0) + 1);
    });
    
    // If no other chunks, return simple frequency (but filter to top words)
    if (allChunks.length === 0) {
      // Return top words by frequency when no corpus for comparison
      const sorted = Array.from(chunkWordCounts.entries())
        .sort((a, b) => b[1] - a[1])
        .slice(0, 10);
      return new Map(sorted);
    }
    
    // Build corpus from all other chunks (excluding current chunk)
    const corpusWords = [];
    const corpusWordCounts = new Map();
    
    allChunks.forEach(chunk => {
      const words = tokenize(chunk.text || chunk);
      words.forEach(word => {
        corpusWords.push(word);
        corpusWordCounts.set(word, (corpusWordCounts.get(word) || 0) + 1);
      });
    });
    
    // Calculate keyness using log-likelihood (G²)
    const keynessScores = new Map();
    const chunkTotalWords = chunkWords.length;
    const corpusTotalWords = corpusWords.length;
    const grandTotal = chunkTotalWords + corpusTotalWords;
    
    // Get all unique words from both chunk and corpus
    const allWords = new Set([...chunkWords, ...corpusWords]);
    
    allWords.forEach(word => {
      // Observed frequencies
      const chunkFreq = chunkWordCounts.get(word) || 0;
      const corpusFreq = corpusWordCounts.get(word) || 0;
      
      // Skip words that don't appear in the chunk
      if (chunkFreq === 0) {
        return;
      }
      
      // Expected frequencies (if word distribution was uniform)
      const expectedChunkFreq = (chunkFreq + corpusFreq) * (chunkTotalWords / grandTotal);
      const expectedCorpusFreq = (chunkFreq + corpusFreq) * (corpusTotalWords / grandTotal);
      
      // Calculate log-likelihood (G²) statistic
      // G² = 2 * Σ [O * ln(O/E)] where O=observed, E=expected
      let g2 = 0;
      
      if (chunkFreq > 0 && expectedChunkFreq > 0) {
        g2 += 2 * chunkFreq * Math.log(chunkFreq / expectedChunkFreq);
      }
      
      if (corpusFreq > 0 && expectedCorpusFreq > 0) {
        g2 += 2 * corpusFreq * Math.log(corpusFreq / expectedCorpusFreq);
      }
      
      // Only keep positive keyness (words more frequent in chunk than expected)
      // Negative values mean word is less frequent than expected
      // Use a small threshold to avoid numerical precision issues
      if (g2 > 0.01 && chunkFreq > expectedChunkFreq) {
        keynessScores.set(word, g2);
      }
    });
    
    return keynessScores;
  }

  /**
   * Get word-level importance scores for highlighting
   * Uses log-likelihood keyness to identify words unusually frequent in this chunk
   * @param {string} chunkText - The chunk text
   * @param {Array} allChunks - All chunks for comparison
   * @returns {Map<string, number>} Word to keyness score
   */
  getWordImportanceScores(chunkText, allChunks = []) {
    return this.calculateKeyness(chunkText, allChunks);
  }

  /**
   * Find text positions for a chunk in the PDF page
   * Uses exact matching first, falls back to embedding-based semantic matching
   * @param {Object} page - PDF.js page object
   * @param {string} chunkText - The chunk text to find
   * @param {Object} viewport - PDF.js viewport object
   * @param {Array} allChunks - All chunks for context (optional, for TF-IDF)
   * @returns {Array} Array of bounding boxes {x, y, width, height, wordScores} in viewport coordinates
   */
  async findChunkTextPositions(page, chunkText, viewport, allChunks = []) {
    // Try exact matching first (fast)
    const exactMatch = await this.findChunkTextPositionsExact(page, chunkText, viewport);
    if (exactMatch.length > 0) {
      // Add word importance scores for highlighting (TF-IDF)
      const wordScores = this.getWordImportanceScores(chunkText, allChunks);
      exactMatch.forEach(bbox => {
        bbox.wordScores = wordScores;
      });
      return exactMatch;
    }
    
    return [];
  }

  /**
   * Exact text matching (original implementation)
   * @param {Object} page - PDF.js page object
   * @param {string} chunkText - The chunk text to find
   * @param {Object} viewport - PDF.js viewport object
   * @returns {Array} Array of bounding boxes
   */
  async findChunkTextPositionsExact(page, chunkText, viewport) {
    // This is the original exact matching logic, moved from findChunkTextPositions
    try {
      // Get text content with coordinates from PDF.js
      const textContent = await page.getTextContent();
      
      if (!textContent || !textContent.items || textContent.items.length === 0) {
        console.warn('No text content found on page');
        return [];
      }

      // Normalize chunk text for matching (remove extra whitespace, lowercase)
      const normalizeText = (text) => {
        return text.toLowerCase().trim().replace(/\s+/g, ' ');
      };
      
      const normalizedChunk = normalizeText(chunkText);
      if (!normalizedChunk || normalizedChunk.length < 10) {
        // Chunk too short, might match too many things
        console.warn('Chunk text too short for reliable matching');
        return [];
      }

      // Build a searchable string from all text items (preserve item indices)
      const allTextItems = textContent.items;
      const allText = allTextItems.map(item => item.str).join(' ');
      const normalizedAllText = normalizeText(allText);
      
      // Try to find the chunk text in the normalized text
      let chunkIndex = normalizedAllText.indexOf(normalizedChunk);
      let searchText = normalizedChunk;
      
      if (chunkIndex === -1) {
        // Try substring matching - use first 100 characters or first 20 words
        const words = normalizedChunk.split(' ');
        const chunkSubstring = words.slice(0, Math.min(20, words.length)).join(' ');
        chunkIndex = normalizedAllText.indexOf(chunkSubstring);
        if (chunkIndex !== -1) {
          searchText = chunkSubstring;
        }
      }
      
      if (chunkIndex === -1) {
        // Try even shorter: first 10 words
        const words = normalizedChunk.split(' ');
        const shortSubstring = words.slice(0, Math.min(10, words.length)).join(' ');
        chunkIndex = normalizedAllText.indexOf(shortSubstring);
        if (chunkIndex !== -1) {
          searchText = shortSubstring;
        }
      }
      
      if (chunkIndex === -1) {
        console.warn(`Chunk text not found on page: "${chunkText.substring(0, 50)}..."`);
        return [];
      }
      
      // Found match, now find the text items that correspond to this position
      return this.findTextItemPositions(allTextItems, searchText, chunkIndex, normalizedAllText, viewport, normalizeText);
      
    } catch (error) {
      console.error('Error finding chunk text positions:', error);
      return [];
    }
  }

  /**
   * Find text item positions that match the search text
   * @param {Array} textItems - Array of text items from PDF.js
   * @param {string} searchText - Normalized text to search for
   * @param {number} textIndex - Character index where searchText was found in normalized text
   * @param {string} normalizedAllText - Full normalized text from all items
   * @param {Object} viewport - PDF.js viewport object
   * @param {Function} normalizeText - Text normalization function
   * @returns {Array} Array of bounding boxes
   */
  findTextItemPositions(textItems, searchText, textIndex, normalizedAllText, viewport, normalizeText) {
    const matches = [];
    
    // Find which text items correspond to the found text
    // We need to map character position back to text items
    let charCount = 0;
    const matchingItems = [];
    
    for (let i = 0; i < textItems.length; i++) {
      const item = textItems[i];
      const normalizedItem = normalizeText(item.str);
      const itemLength = normalizedItem.length + 1; // +1 for space
      
      // Check if this item is within our search range
      if (charCount + normalizedItem.length >= textIndex && 
          charCount <= textIndex + searchText.length) {
        matchingItems.push(item);
      }
      
      charCount += itemLength;
      
      // Stop if we've passed the end of our search text
      if (charCount > textIndex + searchText.length) {
        break;
      }
    }
    
    if (matchingItems.length === 0) {
      // Fallback: try to find items by matching first few words
      const firstWords = searchText.split(' ').slice(0, 5).join(' ');
      let accumulated = '';
      
      for (const item of textItems) {
        const normalizedItem = normalizeText(item.str);
        accumulated += normalizedItem + ' ';
        matchingItems.push(item);
        
        if (normalizeText(accumulated).includes(firstWords)) {
          break;
        }
        
        // Limit to reasonable number of items
        if (matchingItems.length > 50) {
          matchingItems.length = 0;
          break;
        }
      }
    }
    
    if (matchingItems.length > 0) {
      const bbox = this.calculateBoundingBox(matchingItems, viewport);
      if (bbox && bbox.width > 0 && bbox.height > 0) {
        matches.push(bbox);
      }
    }
    
    return matches;
  }

  /**
   * Calculate bounding box from text items and convert to viewport coordinates
   * @param {Array} textItems - Array of text items that form the match
   * @param {Object} viewport - PDF.js viewport object
   * @returns {Object|null} Bounding box {x, y, width, height} in viewport coordinates, or null
   */
  calculateBoundingBox(textItems, viewport) {
    if (!textItems || textItems.length === 0) {
      return null;
    }
    
    // Find min/max coordinates from all text items
    let minX = Infinity, minY = Infinity;
    let maxX = -Infinity, maxY = -Infinity;
    
    for (const item of textItems) {
      if (item.transform && item.transform.length >= 6) {
        // Text items have transform matrix: [a, b, c, d, e, f]
        // e (index 4) is x coordinate, f (index 5) is y coordinate
        // The transform matrix represents: [scaleX, skewY, skewX, scaleY, translateX, translateY]
        const x = item.transform[4]; // translateX (left edge)
        const y = item.transform[5]; // translateY (baseline, bottom of text in PDF coords)
        
        // Get text dimensions
        // Width: use item.width if available, otherwise estimate from transform[0] (scaleX)
        // For PDF.js, item.width is the actual text width in PDF coordinates
        const width = item.width || 0;
        // Height: use item.height if available, otherwise estimate from font size
        // item.height is typically the font size in PDF coordinates
        const height = item.height || (Math.abs(item.transform[3]) || 12);
        
        // PDF coordinate system: origin at bottom-left, Y increases upward
        // y is the baseline (bottom of text), so top is y + height
        // But actually, in PDF.js, y is the baseline, so bottom is y, top is y + height
        minX = Math.min(minX, x);
        minY = Math.min(minY, y); // Bottom edge (baseline)
        maxX = Math.max(maxX, x + width);
        maxY = Math.max(maxY, y + height); // Top edge
      } else if (item.x !== undefined && item.y !== undefined) {
        // Alternative format: direct x, y coordinates
        const x = item.x;
        const y = item.y; // Baseline
        const width = item.width || 0;
        const height = item.height || 12;
        
        minX = Math.min(minX, x);
        minY = Math.min(minY, y); // Bottom
        maxX = Math.max(maxX, x + width);
        maxY = Math.max(maxY, y + height); // Top
      }
    }
    
    if (minX === Infinity || minY === Infinity) {
      return null;
    }
    
    // Convert PDF coordinates to viewport coordinates using PDF.js API
    // PDF coordinates are in points (1/72 inch)
    // PDF coordinate system: origin at bottom-left, Y increases upward
    // Viewport coordinate system: origin at top-left, Y increases downward
    
    // Use viewport's convertToViewportPoint method if available
    let x1, y1, x2, y2;
    
    if (viewport.convertToViewportPoint) {
      // Use PDF.js API for coordinate conversion
      [x1, y1] = viewport.convertToViewportPoint(minX, minY);
      [x2, y2] = viewport.convertToViewportPoint(maxX, maxY);
    } else {
      // Fallback: manual conversion
      // PDF.js viewport already handles scaling, we just need to flip Y
      const pdfPageHeight = viewport.height / viewport.scale;
      
      // Convert PDF coordinates (bottom-left origin) to viewport coordinates (top-left origin)
      x1 = minX * viewport.scale;
      y1 = (pdfPageHeight - maxY) * viewport.scale; // Top edge in viewport
      x2 = maxX * viewport.scale;
      y2 = (pdfPageHeight - minY) * viewport.scale; // Bottom edge in viewport
    }
    
    // Calculate bounding box (already in viewport coordinates)
    const x = Math.min(x1, x2);
    const y = Math.min(y1, y2);
    const width = Math.abs(x2 - x1);
    const height = Math.abs(y2 - y1);
    
    // Ensure minimum dimensions for visibility
    if (width < 1 || height < 1) {
      return null;
    }
    
    return { x, y, width, height };
  }

  /**
   * Add word-level highlights based on TF-IDF scores
   * Highlights individual words within the matched text region
   * @param {HTMLElement} container - Container to add highlights to
   * @param {Object} page - PDF.js page object
   * @param {Object} bbox - Bounding box of matched text
   * @param {Map} wordScores - Map of word to TF-IDF score
   * @param {Object} viewport - PDF.js viewport
   * @param {boolean} isEvidence - Whether this is an evidence chunk
   */
  async addWordLevelHighlights(container, page, bbox, wordScores, viewport, isEvidence) {
    try {
      // Get text content to find individual word positions
      const textContent = await page.getTextContent();
      if (!textContent || !textContent.items) {
        return;
      }
      
      // Filter out common stop words that aren't meaningful for highlighting
      const stopWords = new Set(['the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have', 
        'i', 'it', 'for', 'not', 'on', 'with', 'he', 'as', 'you', 'do', 'at', 'this', 
        'but', 'his', 'by', 'from', 'they', 'we', 'say', 'her', 'she', 'or', 'an', 'will', 
        'my', 'one', 'all', 'would', 'there', 'their', 'what', 'so', 'up', 'out', 'if', 
        'about', 'who', 'get', 'which', 'go', 'me', 'when', 'make', 'can', 'like', 'time', 
        'no', 'just', 'him', 'know', 'take', 'people', 'into', 'year', 'your', 'good', 
        'some', 'could', 'them', 'see', 'other', 'than', 'then', 'now', 'look', 'only', 
        'come', 'its', 'over', 'think', 'also', 'back', 'after', 'use', 'two', 'how', 
        'our', 'work', 'first', 'well', 'way', 'even', 'new', 'want', 'because', 'any', 
        'these', 'give', 'day', 'most', 'us', 'is', 'are', 'was', 'were', 'been', 'being',
        'has', 'had', 'does', 'did', 'may', 'might', 'must', 'shall', 'should', 'could',
        'would', 'can', 'cannot', 'will', 'shall']);
      
      // Ensure wordScores is a Map
      let scoresMap = wordScores;
      if (!(wordScores instanceof Map)) {
        // Convert object to Map if needed
        scoresMap = new Map(Object.entries(wordScores || {}));
      }
      
      // Get top N most important words (highest keyness scores)
      // Keyness identifies words unusually frequent in this chunk vs others
      const sortedWords = Array.from(scoresMap.entries())
        .sort((a, b) => b[1] - a[1])
        .slice(0, 10); // Top 10 most key words (increased from 5)
      
      if (sortedWords.length === 0) {
        console.warn('No key words found for highlighting - keyness scores may be empty. WordScores:', scoresMap);
        return;
      }
      
      console.log(`Found ${sortedWords.length} key words for highlighting:`, sortedWords.map(([w, s]) => `${w}(${s.toFixed(3)})`));
      
      // Normalize scores for opacity calculation
      const maxScore = sortedWords[0][1];
      const minScore = sortedWords[sortedWords.length - 1][1];
      const scoreRange = maxScore - minScore || 1;
      
      // Find text items that match important words and are within the bounding box
      const normalizeWord = (word) => word.toLowerCase().replace(/[^\w]/g, '');
      
      // OPTIMIZATION: Pre-compute normalized words as a Set for O(1) lookup
      const targetWordsSet = new Set();
      const wordToScore = new Map();
      sortedWords.forEach(([word, score]) => {
        const normalizedWord = normalizeWord(word);
        if (normalizedWord.length >= 3) {
          targetWordsSet.add(normalizedWord);
          wordToScore.set(normalizedWord, score);
        }
      });
      
      if (targetWordsSet.size === 0) {
        return; // No valid words to highlight
      }
      
      // OPTIMIZATION: Pre-filter items by bounding box first (spatial filtering)
      // This reduces the number of items we need to check for word matching
      const tolerance = 0.10;
      const bboxLeft = bbox.x - (bbox.width * tolerance);
      const bboxRight = bbox.x + bbox.width + (bbox.width * tolerance);
      const bboxTop = bbox.y - (bbox.height * tolerance);
      const bboxBottom = bbox.y + bbox.height + (bbox.height * tolerance);
      
      // Pre-compute viewport conversion function
      const pdfPageHeight = viewport.height / viewport.scale;
      const convertToViewport = (x, y, width, height) => {
        if (viewport.convertToViewportPoint) {
          const [itemX, itemY] = viewport.convertToViewportPoint(x, y);
          const itemRight = x + width;
          const itemTop = y + height;
          const [itemX2, itemY2] = viewport.convertToViewportPoint(itemRight, itemTop);
          return {
            x: itemX,
            y: itemY,
            width: Math.abs(itemX2 - itemX),
            height: Math.abs(itemY2 - itemY)
          };
        } else {
          return {
            x: x * viewport.scale,
            y: (pdfPageHeight - (y + height)) * viewport.scale,
            width: width * viewport.scale,
            height: height * viewport.scale
          };
        }
      };
      
      let matchesFound = 0;
      const maxMatches = 50; // Limit total highlights to prevent performance issues
      
      // Single pass through items: filter by bbox first, then match words
      for (const item of textContent.items) {
        if (matchesFound >= maxMatches) break; // Early exit if we've found enough
        
        if (!item.transform || item.transform.length < 6) continue;
        
        const x = item.transform[4];
        const y = item.transform[5];
        const width = item.width || 0;
        const height = item.height || (Math.abs(item.transform[3]) || 12);
        
        // Quick bounding box check in PDF coordinates (before viewport conversion)
        // This is a rough filter - we'll do precise check after conversion
        const itemRight = x + width;
        const itemTop = y + height;
        
        // Convert to viewport coordinates
        const viewportCoords = convertToViewport(x, y, width, height);
        const itemX = viewportCoords.x;
        const itemY = viewportCoords.y;
        const itemW = viewportCoords.width;
        const itemH = viewportCoords.height;
        
        // Precise bounding box check
        if (itemX < bboxLeft || itemX + itemW > bboxRight ||
            itemY < bboxTop || itemY + itemH > bboxBottom) {
          continue; // Skip items outside bounding box
        }
        
        // Now check if the word matches (only for items within bbox)
        const itemText = normalizeWord(item.str);
        if (targetWordsSet.has(itemText)) {
          // Exact match found
          const score = wordToScore.get(itemText);
          const normalizedScore = (score - minScore) / scoreRange;
          const opacity = 0.5 + (normalizedScore * 0.4);
          
          // Create word highlight
          const wordHighlight = document.createElement('div');
          wordHighlight.className = `word-highlight ${isEvidence ? 'evidence-word' : ''}`;
          
          wordHighlight.style.left = `${(itemX / viewport.width) * 100}%`;
          wordHighlight.style.top = `${(itemY / viewport.height) * 100}%`;
          wordHighlight.style.width = `${(itemW / viewport.width) * 100}%`;
          wordHighlight.style.height = `${(itemH / viewport.height) * 100}%`;
          wordHighlight.style.opacity = opacity;
          wordHighlight.style.backgroundColor = isEvidence 
            ? 'rgba(255, 200, 0, 0.7)'
            : 'rgba(255, 255, 0, 0.6)';
          wordHighlight.style.borderRadius = '2px';
          wordHighlight.title = `Important word: "${item.str}" (Keyness: ${score.toFixed(3)})`;
          
          container.appendChild(wordHighlight);
          matchesFound++;
        } else {
          // Also check for partial matches (starts/ends with) but only for items in bbox
          for (const normalizedWord of targetWordsSet) {
            if (itemText.startsWith(normalizedWord) || itemText.endsWith(normalizedWord)) {
              const score = wordToScore.get(normalizedWord);
              const normalizedScore = (score - minScore) / scoreRange;
              const opacity = 0.5 + (normalizedScore * 0.4);
              
              const wordHighlight = document.createElement('div');
              wordHighlight.className = `word-highlight ${isEvidence ? 'evidence-word' : ''}`;
              
              wordHighlight.style.left = `${(itemX / viewport.width) * 100}%`;
              wordHighlight.style.top = `${(itemY / viewport.height) * 100}%`;
              wordHighlight.style.width = `${(itemW / viewport.width) * 100}%`;
              wordHighlight.style.height = `${(itemH / viewport.height) * 100}%`;
              wordHighlight.style.opacity = opacity;
              wordHighlight.style.backgroundColor = isEvidence 
                ? 'rgba(255, 200, 0, 0.7)'
                : 'rgba(255, 255, 0, 0.6)';
              wordHighlight.style.borderRadius = '2px';
              wordHighlight.title = `Important word: "${item.str}" (Keyness: ${score.toFixed(3)})`;
              
              container.appendChild(wordHighlight);
              matchesFound++;
              break; // Only match once per item
            }
          }
        }
      }
      
      console.log(`Added ${matchesFound} word highlights for ${sortedWords.length} key words`);
    } catch (error) {
      console.error('Error adding word-level highlights:', error);
    }
  }

  async navigateToPage(pageNum) {
    // Preserve filter states BEFORE any changes
    const preservedQuestionId = this._selectedQuestionId;
    const preservedShowEvidenceOnly = this._showEvidenceOnly;
    
    this._currentPage = pageNum;
    
    // Render will read from instance variables, so state is already preserved
    await this.render();
    
    // Ensure state is still preserved (defensive)
    this._selectedQuestionId = preservedQuestionId;
    this._showEvidenceOnly = preservedShowEvidenceOnly;
    
    // Update the form controls to reflect preserved state (after render completes)
    // Use requestAnimationFrame to ensure DOM is ready
    requestAnimationFrame(() => {
      const questionSelect = this.shadowRoot?.getElementById('question-select');
      if (questionSelect) {
        questionSelect.value = preservedQuestionId || '';
      }
      const evidenceFilter = this.shadowRoot?.getElementById('evidence-filter');
      if (evidenceFilter) {
        evidenceFilter.checked = preservedShowEvidenceOnly;
      }
    });
  }

  async navigateToChunk(chunk) {
    // CRITICAL: Preserve filter states BEFORE navigation to prevent reset
    const preservedQuestionId = this._selectedQuestionId;
    const preservedShowEvidenceOnly = this._showEvidenceOnly;
    
    // Extract page number from metadata - handle both 'page_number' and 'source' fields
    let pageNum = 1;
    if (chunk.metadata) {
      if (chunk.metadata.page_number !== undefined) {
        pageNum = parseInt(chunk.metadata.page_number) || 1;
      } else if (chunk.metadata.source !== undefined) {
        // PyMuPDFReader uses 'source' as page number string
        pageNum = parseInt(chunk.metadata.source) || 1;
      }
    }
    
    // Ensure page number is within valid range
    if (this._pdfDoc) {
      const totalPages = this._pdfDoc.numPages;
      if (pageNum < 1) pageNum = 1;
      if (pageNum > totalPages) pageNum = totalPages;
    }
    
    // Navigate to page (which will preserve state)
    await this.navigateToPage(pageNum);
    
    // Ensure state is still preserved after navigation
    this._selectedQuestionId = preservedQuestionId;
    this._showEvidenceOnly = preservedShowEvidenceOnly;
    
    // Dispatch event for chunk selection
    this.dispatchEvent(new CustomEvent('chunk-selected', {
      detail: { chunk, pageNum },
      bubbles: true,
      composed: true
    }));
  }

  // Public API: Navigate to chunk by ID (for Streamlit communication)
  // chunkId format: "question_id_chunk_order" (e.g., "tcfd_1_0")
  // Note: question_id may contain underscores, so we split from the right
  async navigateToChunkById(chunkId) {
    if (!chunkId) return;
    
    // Parse chunk ID: format is "question_id_chunk_order"
    // Since question_id may contain underscores, find the last underscore
    const lastUnderscoreIndex = chunkId.lastIndexOf('_');
    if (lastUnderscoreIndex === -1) {
      console.warn(`Invalid chunk ID format: ${chunkId}. Expected format: "question_id_chunk_order"`);
      return;
    }
    
    // Split: everything before last underscore is question_id, after is chunk_order
    const questionId = chunkId.substring(0, lastUnderscoreIndex);
    const chunkOrderStr = chunkId.substring(lastUnderscoreIndex + 1);
    const chunkOrder = parseInt(chunkOrderStr);
    
    if (isNaN(chunkOrder)) {
      console.warn(`Invalid chunk order in chunk ID: ${chunkId} (parsed as: ${chunkOrderStr})`);
      return;
    }
    
    // Find the chunk - match by question_id and chunk_order
    const chunk = this._chunks.find(c => {
      const cQuestionId = c.question_id || '';
      const cChunkOrder = c.chunk_order !== undefined ? c.chunk_order : -1;
      // Match question_id exactly and chunk_order (accounting for 0-based vs 1-based)
      return cQuestionId === questionId && 
             (cChunkOrder === chunkOrder || cChunkOrder === chunkOrder - 1 || cChunkOrder === chunkOrder + 1);
    });
    
    if (!chunk) {
      console.warn(`Chunk not found for ID: ${chunkId} (question_id: ${questionId}, chunk_order: ${chunkOrder})`);
      console.debug('Available chunks:', this._chunks.map(c => ({ 
        question_id: c.question_id, 
        chunk_order: c.chunk_order 
      })));
      return;
    }
    
    // CRITICAL: Preserve filter states before navigation
    const preservedShowEvidenceOnly = this._showEvidenceOnly;
    
    // Set the selected question ID first (this will filter chunks)
    this.setSelectedQuestionId(questionId);
    
    // Wait a bit for the filter to apply, then navigate to chunk
    await new Promise(resolve => setTimeout(resolve, 100));
    
    // Navigate to the chunk (this will preserve filter state)
    await this.navigateToChunk(chunk);
    
    // Restore evidence filter state
    this._showEvidenceOnly = preservedShowEvidenceOnly;
    
    // Set highlighted chunk ID for visual emphasis
    this._highlightedChunkId = chunkId;
  }

  async render() {
    if (!this.shadowRoot) return;

    // Preserve filter states before rendering (in case render is called from navigation)
    const preservedQuestionId = this._selectedQuestionId;
    const preservedShowEvidenceOnly = this._showEvidenceOnly;

    const filteredChunks = this.getFilteredChunks();
    
    // Group chunks by page
    const chunksByPage = {};
    filteredChunks.forEach(chunk => {
      // Extract page number from metadata - handle both 'page_number' and 'source' fields
      let pageNum = 1;
      if (chunk.metadata) {
        if (chunk.metadata.page_number !== undefined) {
          pageNum = parseInt(chunk.metadata.page_number) || 1;
        } else if (chunk.metadata.source !== undefined) {
          // PyMuPDFReader uses 'source' as page number string
          pageNum = parseInt(chunk.metadata.source) || 1;
        }
      }
      if (!chunksByPage[pageNum]) {
        chunksByPage[pageNum] = [];
      }
      chunksByPage[pageNum].push(chunk);
    });

    const style = `
      <style>
        :host {
          display: flex;
          width: 100%;
          height: 100%;
          font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        }
        .container {
          display: flex;
          width: 100%;
          height: 100%;
          background: #f5f5f5;
        }
        .sidebar {
          width: 350px;
          background: white;
          border-right: 1px solid #e0e0e0;
          display: flex;
          flex-direction: column;
          overflow: hidden;
        }
        .sidebar-header {
          padding: 16px;
          border-bottom: 1px solid #e0e0e0;
          background: #fafafa;
        }
        .sidebar-header h3 {
          margin: 0 0 12px 0;
          font-size: 16px;
          font-weight: 600;
          color: #333;
        }
        .question-selector {
          margin-bottom: 12px;
        }
        .question-selector select {
          width: 100%;
          padding: 8px 12px;
          border: 1px solid #ddd;
          border-radius: 4px;
          font-size: 14px;
          background: white;
        }
        .evidence-filter {
          display: flex;
          align-items: center;
          gap: 8px;
        }
        .evidence-filter input[type="checkbox"] {
          width: 18px;
          height: 18px;
          cursor: pointer;
        }
        .evidence-filter label {
          font-size: 14px;
          color: #666;
          cursor: pointer;
        }
        .chunks-list {
          flex: 1;
          overflow-y: auto;
          padding: 8px;
        }
        .chunk-item {
          padding: 12px;
          margin-bottom: 8px;
          border: 1px solid #e0e0e0;
          border-radius: 6px;
          cursor: pointer;
          transition: all 0.2s;
          background: white;
        }
        .chunk-item:hover {
          border-color: #4313C8;
          box-shadow: 0 2px 4px rgba(67, 19, 200, 0.1);
        }
        .chunk-item.evidence {
          border-left: 4px solid #4313C8;
          background: #f8f7ff;
        }
        .chunk-item .chunk-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 8px;
        }
        .chunk-item .chunk-title {
          font-weight: 600;
          font-size: 14px;
          color: #333;
        }
        .chunk-item .chunk-badge {
          padding: 2px 8px;
          border-radius: 12px;
          font-size: 11px;
          font-weight: 600;
        }
        .chunk-item .chunk-badge.evidence {
          background: #4313C8;
          color: white;
        }
        .chunk-item .chunk-badge.page {
          background: #e0e0e0;
          color: #666;
        }
        .chunk-item .chunk-text {
          font-size: 13px;
          color: #666;
          line-height: 1.5;
          display: -webkit-box;
          -webkit-line-clamp: 3;
          -webkit-box-orient: vertical;
          overflow: hidden;
        }
        .chunk-item .chunk-scores {
          display: flex;
          gap: 12px;
          margin-top: 8px;
          font-size: 11px;
          color: #999;
        }
        .viewer {
          flex: 1;
          display: flex;
          flex-direction: column;
          overflow: hidden;
          background: #525252;
        }
        .viewer-controls {
          padding: 12px 16px;
          background: white;
          border-bottom: 1px solid #e0e0e0;
          display: flex;
          align-items: center;
          gap: 12px;
        }
        .viewer-controls button {
          padding: 6px 12px;
          border: 1px solid #ddd;
          border-radius: 4px;
          background: white;
          cursor: pointer;
          font-size: 14px;
        }
        .viewer-controls button:hover {
          background: #f5f5f5;
        }
        .viewer-controls .page-info {
          margin: 0 12px;
          font-size: 14px;
          color: #666;
        }
        .viewer-content {
          flex: 1;
          overflow: auto;
          display: flex;
          justify-content: center;
          align-items: flex-start;
          padding: 20px;
        }
        .page-container {
          position: relative;
          margin-bottom: 20px;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
          background: white;
        }
        .page-canvas {
          display: block;
        }
        .page-highlights {
          position: absolute;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
          pointer-events: none;
        }
        .highlight {
          position: absolute;
          background: rgba(67, 19, 200, 0.2);
          border: 2px solid rgba(67, 19, 200, 0.5);
        }
        .highlight {
          pointer-events: none;
          z-index: 1;
        }
        .highlight.evidence {
          background: rgba(67, 19, 200, 0.3);
          border-color: #4313C8;
        }
        .word-highlight {
          position: absolute;
          pointer-events: none;
          z-index: 2;
          transition: opacity 0.2s;
          border-radius: 2px;
        }
        .word-highlight.evidence-word {
          background: rgba(255, 200, 0, 0.6) !important;
        }
        .loading {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          height: 100%;
          color: #666;
          font-size: 14px;
        }
        .spinner {
          border: 3px solid #f3f3f3;
          border-top: 3px solid #4313C8;
          border-radius: 50%;
          width: 40px;
          height: 40px;
          animation: spin 1s linear infinite;
          margin-bottom: 16px;
        }
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
        .loading-text {
          margin-top: 8px;
          color: #666;
        }
        .error {
          display: flex;
          align-items: center;
          justify-content: center;
          height: 100%;
          color: #d32f2f;
          font-size: 14px;
        }
      </style>
    `;

    const html = `
      <div class="container">
        <div class="sidebar">
          <div class="sidebar-header">
            <h3>Chunks by Question</h3>
            <div class="question-selector">
              <select id="question-select">
                <option value="">All Questions</option>
                ${this._questions.map(q => `
                  <option value="${q.question_id}" ${this._selectedQuestionId === q.question_id ? 'selected' : ''}>
                    ${q.text ? q.text.substring(0, 50) + '...' : q.question_id}
                  </option>
                `).join('')}
              </select>
            </div>
            <div class="evidence-filter">
              <input type="checkbox" id="evidence-filter" ${this._showEvidenceOnly ? 'checked' : ''}>
              <label for="evidence-filter">Show evidence only</label>
            </div>
          </div>
          <div class="chunks-list">
            ${filteredChunks.length === 0 ? '<div style="padding: 16px; color: #999; text-align: center;">No chunks to display</div>' : ''}
            ${filteredChunks.map((chunk, idx) => {
              // Extract page number from metadata - handle both 'page_number' and 'source' fields
              let pageNum = '?';
              if (chunk.metadata) {
                if (chunk.metadata.page_number !== undefined) {
                  pageNum = parseInt(chunk.metadata.page_number) || '?';
                } else if (chunk.metadata.source !== undefined) {
                  // PyMuPDFReader uses 'source' as page number string
                  pageNum = parseInt(chunk.metadata.source) || '?';
                }
              }
              
              const isEvidence = chunk.is_evidence === true;
              const similarityScore = chunk.similarity_score?.toFixed(3) || 'N/A';
              const llmScore = chunk.llm_score?.toFixed(3) || 'N/A';
              const chunkText = chunk.text || '';
              const preview = chunkText.substring(0, 150) + (chunkText.length > 150 ? '...' : '');
              
              return `
                <div class="chunk-item ${isEvidence ? 'evidence' : ''}" data-chunk-index="${idx}">
                  <div class="chunk-header">
                    <span class="chunk-title">Chunk ${chunk.chunk_order !== undefined ? chunk.chunk_order + 1 : idx + 1}</span>
                    <div style="display: flex; gap: 4px;">
                      ${isEvidence ? `<span class="chunk-badge evidence">Evidence</span>` : ''}
                      <span class="chunk-badge page">Page ${pageNum}</span>
                    </div>
                  </div>
                  <div class="chunk-text">${this.escapeHtml(preview)}</div>
                  <div class="chunk-scores">
                    <span>Similarity: ${similarityScore}</span>
                    ${chunk.llm_score !== null && chunk.llm_score !== undefined ? `<span>LLM: ${llmScore}</span>` : ''}
                  </div>
                </div>
              `;
            }).join('')}
          </div>
        </div>
        <div class="viewer">
          <div class="viewer-controls">
            <button id="prev-page">Previous</button>
            <span class="page-info">
              Page <span id="current-page">${this._currentPage}</span> of <span id="total-pages">-</span>
            </span>
            <button id="next-page">Next</button>
          </div>
          <div class="viewer-content" id="viewer-content">
            <div class="loading">Loading PDF...</div>
          </div>
        </div>
      </div>
    `;

    this.shadowRoot.innerHTML = style + html;

    // CRITICAL: Restore filter states immediately after rendering HTML
    // This ensures instance variables are correct before any other code runs
    this._selectedQuestionId = preservedQuestionId;
    this._showEvidenceOnly = preservedShowEvidenceOnly;
    
    // Set up event listeners first (before updating form controls)
    this.setupEventListeners();
    
    // Update form controls to reflect preserved state AFTER listeners are attached
    // Use setTimeout to ensure DOM is fully ready
    setTimeout(() => {
      const questionSelect = this.shadowRoot.getElementById('question-select');
      if (questionSelect && this._selectedQuestionId !== undefined) {
        questionSelect.value = this._selectedQuestionId || '';
      }
      const evidenceFilter = this.shadowRoot.getElementById('evidence-filter');
      if (evidenceFilter && this._showEvidenceOnly !== undefined) {
        evidenceFilter.checked = this._showEvidenceOnly;
      }
    }, 0);
    
    // Load and render PDF
    this.loadAndRenderPdf();
  }

  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  setupEventListeners() {
    // Question selector
    const questionSelect = this.shadowRoot.getElementById('question-select');
    if (questionSelect) {
      questionSelect.addEventListener('change', (e) => {
        // Use skipRender=true to prevent full PDF reload when filter changes
        this.setSelectedQuestionId(e.target.value || null, true);
      });
    }

    // Evidence filter
    const evidenceFilter = this.shadowRoot.getElementById('evidence-filter');
    if (evidenceFilter) {
      evidenceFilter.addEventListener('change', (e) => {
        // Use skipRender=true to prevent full PDF reload when filter changes
        this.setShowEvidenceOnly(e.target.checked, true);
      });
    }

    // Chunk items - use the new attachChunkListeners method
    this.attachChunkListeners();

    // Page navigation
    const prevBtn = this.shadowRoot.getElementById('prev-page');
    const nextBtn = this.shadowRoot.getElementById('next-page');
    
    if (prevBtn) {
      prevBtn.addEventListener('click', () => {
        if (this._currentPage > 1) {
          this.navigateToPage(this._currentPage - 1);
        }
      });
    }

    if (nextBtn) {
      nextBtn.addEventListener('click', async () => {
        if (this._pdfDoc) {
          const totalPages = this._pdfDoc.numPages;
          if (this._currentPage < totalPages) {
            await this.navigateToPage(this._currentPage + 1);
          }
        }
      });
    }
  }

  async loadAndRenderPdf() {
    try {
      // Set loading state at start
      this._isLoading = true;
      this.updateLoadingDisplay();
      
      const pdfDoc = await this.loadPdf();
      const totalPages = pdfDoc.numPages;
      
      // Update total pages
      const totalPagesEl = this.shadowRoot.getElementById('total-pages');
      if (totalPagesEl) {
        totalPagesEl.textContent = totalPages;
      }

      // Render current page and nearby pages
      await this.renderCurrentPage();
      
      // Clear loading state after rendering
      this._isLoading = false;
      // renderCurrentPage will update the content, so we don't need to call updateLoadingDisplay
    } catch (error) {
      this._isLoading = false;
      const viewerContent = this.shadowRoot.getElementById('viewer-content');
      if (viewerContent) {
        viewerContent.innerHTML = `<div class="error">Error loading PDF: ${error.message}</div>`;
      }
    }
  }

  async renderCurrentPage() {
    const viewerContent = this.shadowRoot.getElementById('viewer-content');
    if (!viewerContent) return;

    try {
      const pdfDoc = await this.loadPdf();
      const totalPages = pdfDoc.numPages;
      
      if (this._currentPage < 1) this._currentPage = 1;
      if (this._currentPage > totalPages) this._currentPage = totalPages;

      // Update current page display
      const currentPageEl = this.shadowRoot.getElementById('current-page');
      if (currentPageEl) {
        currentPageEl.textContent = this._currentPage;
      }

      // Render the current page
      const sourceCanvas = await this.renderPage(this._currentPage);
      if (!sourceCanvas) {
        viewerContent.innerHTML = '<div class="error">Error rendering page</div>';
        return;
      }

      // Get the page object for text extraction (needed for highlighting)
      const page = await pdfDoc.getPage(this._currentPage);
      const viewport = page.getViewport({ scale: this._scale });

      // Get chunks for this page
      const filteredChunks = this.getFilteredChunks();
      const pageChunks = filteredChunks.filter(c => {
        // Extract page number from metadata - handle both 'page_number' and 'source' fields
        let pageNum = 1;
        if (c.metadata) {
          if (c.metadata.page_number !== undefined) {
            pageNum = parseInt(c.metadata.page_number) || 1;
          } else if (c.metadata.source !== undefined) {
            // PyMuPDFReader uses 'source' as page number string
            pageNum = parseInt(c.metadata.source) || 1;
          }
        }
        return pageNum === this._currentPage;
      });

      // Create page container with highlights
      const pageContainer = document.createElement('div');
      pageContainer.className = 'page-container';
      
      // Create a new canvas and copy the image data from the rendered canvas
      const displayCanvas = document.createElement('canvas');
      displayCanvas.className = 'page-canvas';
      displayCanvas.width = sourceCanvas.width;
      displayCanvas.height = sourceCanvas.height;
      const displayCtx = displayCanvas.getContext('2d');
      displayCtx.drawImage(sourceCanvas, 0, 0);
      pageContainer.appendChild(displayCanvas);

      // Add highlights overlay with actual text positions and word-level highlighting
      if (pageChunks.length > 0) {
        const highlightsDiv = document.createElement('div');
        highlightsDiv.className = 'page-highlights';
        
        // Get all chunks for TF-IDF context (all chunks from all questions, not just this page)
        const allChunksForTFIDF = filteredChunks.map(c => ({ text: c.text || '' }));
        
        // Process each chunk to find its text position
        for (const chunk of pageChunks) {
          const chunkText = chunk.text || '';
          if (!chunkText || chunkText.trim().length === 0) {
            continue;
          }
          
          // Find text positions for this chunk (with TF-IDF context)
          const boundingBoxes = await this.findChunkTextPositions(
            page, 
            chunkText, 
            viewport, 
            allChunksForTFIDF
          );
          
          if (boundingBoxes.length > 0) {
            // Create highlight divs for each bounding box
            boundingBoxes.forEach((bbox) => {
              // Main chunk highlight (background)
              const highlight = document.createElement('div');
              highlight.className = `highlight ${chunk.is_evidence === true || chunk.is_evidence === 1 ? 'evidence' : ''}`;
              
              // Position highlight at calculated coordinates
              const xPercent = (bbox.x / viewport.width) * 100;
              const yPercent = (bbox.y / viewport.height) * 100;
              const widthPercent = (bbox.width / viewport.width) * 100;
              const heightPercent = (bbox.height / viewport.height) * 100;
              
              highlight.style.left = `${xPercent}%`;
              highlight.style.top = `${yPercent}%`;
              highlight.style.width = `${widthPercent}%`;
              highlight.style.height = `${heightPercent}%`;
              
              highlight.title = chunk.is_evidence === true || chunk.is_evidence === 1 
                ? `Evidence chunk: ${chunkText.substring(0, 50)}...` 
                : `Chunk: ${chunkText.substring(0, 50)}...`;
              
              highlightsDiv.appendChild(highlight);
              
              // Add word-level highlights if we have word scores
              // Check if wordScores is a Map and has entries
              const hasWordScores = bbox.wordScores && 
                (bbox.wordScores instanceof Map ? bbox.wordScores.size > 0 : Object.keys(bbox.wordScores || {}).length > 0);
              
              if (hasWordScores) {
                console.log(`Adding word highlights for chunk with ${bbox.wordScores instanceof Map ? bbox.wordScores.size : Object.keys(bbox.wordScores || {}).length} word scores`);
                this.addWordLevelHighlights(
                  highlightsDiv,
                  page,
                  bbox,
                  bbox.wordScores,
                  viewport,
                  chunk.is_evidence === true || chunk.is_evidence === 1
                );
              } else {
                console.warn('No wordScores found for chunk, skipping word highlights');
              }
            });
          } else {
            // Fallback: if text not found, show a small indicator
            console.warn(`Could not find text position for chunk on page ${this._currentPage}`);
            const highlight = document.createElement('div');
            highlight.className = `highlight ${chunk.is_evidence === true || chunk.is_evidence === 1 ? 'evidence' : ''}`;
            highlight.style.top = '5%';
            highlight.style.left = '5%';
            highlight.style.width = '10px';
            highlight.style.height = '10px';
            highlight.style.borderRadius = '50%';
            highlight.title = 'Chunk text position not found';
            highlightsDiv.appendChild(highlight);
          }
        }
        
        pageContainer.appendChild(highlightsDiv);
      }

      viewerContent.innerHTML = '';
      viewerContent.appendChild(pageContainer);

    } catch (error) {
      console.error('Error rendering current page:', error);
      viewerContent.innerHTML = `<div class="error">Error rendering page: ${error.message}</div>`;
    }
  }
}

// Register the custom element
if (!customElements.get('pdf-viewer-with-chunks')) {
  customElements.define('pdf-viewer-with-chunks', PdfViewerWithChunks);
}

export default PdfViewerWithChunks;

