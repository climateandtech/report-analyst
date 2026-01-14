class B extends HTMLElement {
  constructor() {
    super(), this.attachShadow({ mode: "open" }), this._pdfUrl = null, this._pdfData = null, this._chunks = [], this._questions = [], this._selectedQuestionId = null, this._showEvidenceOnly = !1, this._pdfDoc = null, this._currentPage = 1, this._scale = 1.5, this._pdfjsLib = null, this._renderedPages = /* @__PURE__ */ new Map(), this._isLoading = !1, this._highlightedChunkId = null;
  }
  static get observedAttributes() {
    return ["pdf-url", "pdf-data", "chunks", "questions", "selected-question-id", "show-evidence-only"];
  }
  connectedCallback() {
    this.loadPdfJs().then(() => {
      this.render();
    });
  }
  disconnectedCallback() {
    this._renderedPages.clear(), this._pdfDoc && (this._pdfDoc.destroy(), this._pdfDoc = null);
  }
  attributeChangedCallback(e, t, s) {
    if (t !== s)
      try {
        e === "pdf-url" ? (this._pdfUrl = s, this._pdfData = null) : e === "pdf-data" ? (this._pdfData = s, this._pdfUrl = null) : e === "chunks" ? this._chunks = s ? JSON.parse(s) : [] : e === "questions" ? this._questions = s ? JSON.parse(s) : [] : e === "selected-question-id" ? this._selectedQuestionId = s : e === "show-evidence-only" && (this._showEvidenceOnly = s === "true" || s === ""), this._skipAttributeRender || this.render();
      } catch (i) {
        console.error(`Error parsing ${e}:`, i);
      }
  }
  // Public API: Set PDF URL
  setPdfUrl(e) {
    this._pdfUrl = e, this._pdfData = null, this.setAttribute("pdf-url", e);
  }
  // Public API: Set PDF data (base64)
  setPdfData(e) {
    this._pdfData = e, this._pdfUrl = null, this.setAttribute("pdf-data", e);
  }
  // Public API: Set chunks
  setChunks(e) {
    this._chunks = e, this.setAttribute("chunks", JSON.stringify(e));
  }
  // Public API: Set questions
  setQuestions(e) {
    this._questions = e, this.setAttribute("questions", JSON.stringify(e));
  }
  // Public API: Set selected question
  setSelectedQuestionId(e, t = !1) {
    this._selectedQuestionId = e, t ? (this._skipAttributeRender = !0, this.setAttribute("selected-question-id", e || ""), this._skipAttributeRender = !1, this.updateFilterUI()) : this.setAttribute("selected-question-id", e || "");
  }
  // Public API: Set evidence filter
  setShowEvidenceOnly(e, t = !1) {
    this._showEvidenceOnly = e, t ? (this._skipAttributeRender = !0, this.setAttribute("show-evidence-only", e ? "true" : "false"), this._skipAttributeRender = !1, this.updateFilterUI()) : this.setAttribute("show-evidence-only", e ? "true" : "false");
  }
  // Update filter UI without full render
  updateFilterUI() {
    var s, i;
    const e = (s = this.shadowRoot) == null ? void 0 : s.getElementById("question-select");
    e && (e.value = this._selectedQuestionId || "");
    const t = (i = this.shadowRoot) == null ? void 0 : i.getElementById("evidence-filter");
    t && (t.checked = this._showEvidenceOnly), this.renderChunkList();
  }
  // Render only the chunk list without re-rendering PDF
  renderChunkList() {
    var s;
    const e = (s = this.shadowRoot) == null ? void 0 : s.querySelector(".chunks-list");
    if (!e) return;
    const t = this.getFilteredChunks();
    e.innerHTML = t.length === 0 ? '<div style="padding: 16px; color: #999; text-align: center;">No chunks to display</div>' : t.map((i, n) => {
      var g, c;
      let r = "?";
      i.metadata && (i.metadata.page_number !== void 0 ? r = parseInt(i.metadata.page_number) || "?" : i.metadata.source !== void 0 && (r = parseInt(i.metadata.source) || "?"));
      const o = i.is_evidence === !0, l = ((g = i.similarity_score) == null ? void 0 : g.toFixed(3)) || "N/A", h = ((c = i.llm_score) == null ? void 0 : c.toFixed(3)) || "N/A", a = i.text || "", p = a.substring(0, 150) + (a.length > 150 ? "..." : "");
      return `
            <div class="chunk-item ${o ? "evidence" : ""}" data-chunk-index="${n}">
              <div class="chunk-header">
                <span class="chunk-title">Chunk ${i.chunk_order !== void 0 ? i.chunk_order + 1 : n + 1}</span>
                <div style="display: flex; gap: 4px;">
                  ${o ? '<span class="chunk-badge evidence">Evidence</span>' : ""}
                  <span class="chunk-badge page">Page ${r}</span>
                </div>
              </div>
              <div class="chunk-text">${this.escapeHtml(p)}</div>
              <div class="chunk-scores">
                <span>Similarity: ${l}</span>
                ${i.llm_score !== null && i.llm_score !== void 0 ? `<span>LLM: ${h}</span>` : ""}
              </div>
            </div>
          `;
    }).join(""), this.attachChunkListeners();
  }
  // Attach click listeners to chunk items
  attachChunkListeners() {
    var t;
    const e = (t = this.shadowRoot) == null ? void 0 : t.querySelectorAll(".chunk-item");
    e && e.forEach((s) => {
      var n;
      const i = s.cloneNode(!0);
      (n = s.parentNode) == null || n.replaceChild(i, s), i.addEventListener("click", () => {
        const r = parseInt(i.dataset.chunkIndex), o = this.getFilteredChunks()[r];
        o && this.navigateToChunk(o);
      });
    });
  }
  async loadPdfJs() {
    if (!this._pdfjsLib) {
      if (typeof pdfjsLib > "u") {
        const e = document.createElement("script");
        e.src = "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js", e.async = !0, await new Promise((t, s) => {
          e.onload = t, e.onerror = s, document.head.appendChild(e);
        });
      }
      this._pdfjsLib = window.pdfjsLib || pdfjsLib, this._pdfjsLib.GlobalWorkerOptions && (this._pdfjsLib.GlobalWorkerOptions.workerSrc = "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js"), this._pdfjsLib.GlobalWorkerOptions && (this._pdfjsLib.GlobalWorkerOptions.cMapUrl = "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/cmaps/", this._pdfjsLib.GlobalWorkerOptions.cMapPacked = !0);
    }
  }
  async loadPdf() {
    if (this._pdfjsLib || await this.loadPdfJs(), this._pdfDoc)
      return this._pdfDoc;
    this._isLoading = !0, this.updateLoadingDisplay();
    try {
      let e;
      const t = {
        cMapUrl: "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/cmaps/",
        cMapPacked: !0,
        standardFontDataUrl: "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/standard_fonts/"
      };
      if (this._pdfData) {
        const s = this._pdfData.replace(/^data:application\/pdf;base64,/, ""), i = atob(s), n = new Uint8Array(i.length);
        for (let r = 0; r < i.length; r++)
          n[r] = i.charCodeAt(r);
        e = this._pdfjsLib.getDocument({
          data: n,
          ...t
        });
      } else if (this._pdfUrl)
        e = this._pdfjsLib.getDocument({
          url: this._pdfUrl,
          ...t
        });
      else
        throw new Error("No PDF URL or data provided");
      return this._pdfDoc = await e.promise, this._pdfDoc;
    } catch (e) {
      throw console.error("Error loading PDF:", e), e;
    }
  }
  updateLoadingDisplay() {
    var t;
    const e = (t = this.shadowRoot) == null ? void 0 : t.getElementById("viewer-content");
    e && this._isLoading && (e.innerHTML = `
        <div class="loading">
          <div class="spinner"></div>
          <div class="loading-text">Loading PDF...</div>
        </div>
      `);
  }
  getFilteredChunks() {
    let e = [];
    if (this._selectedQuestionId) {
      const t = this._questions.find((s) => s.question_id === this._selectedQuestionId);
      t && t.chunks ? e = t.chunks : e = this._chunks.filter((s) => s.question_id === this._selectedQuestionId);
    } else
      e = this._chunks;
    return this._showEvidenceOnly && (e = e.filter((t) => t.is_evidence === !0 || t.is_evidence === 1)), e;
  }
  async renderPage(e) {
    if (this._renderedPages.has(e))
      return this._renderedPages.get(e);
    try {
      const s = await (await this.loadPdf()).getPage(e), i = s.getViewport({ scale: this._scale }), n = document.createElement("canvas"), r = n.getContext("2d");
      return n.height = i.height, n.width = i.width, await s.render({
        canvasContext: r,
        viewport: i
      }).promise, this._renderedPages.set(e, n), n;
    } catch (t) {
      return console.error(`Error rendering page ${e}:`, t), null;
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
  calculateKeyness(e, t = []) {
    const s = (c) => c.toLowerCase().replace(/[^\w\s]/g, " ").split(/\s+/).filter((f) => f.length > 2), i = s(e), n = /* @__PURE__ */ new Map();
    if (i.forEach((c) => {
      n.set(c, (n.get(c) || 0) + 1);
    }), t.length === 0) {
      const c = Array.from(n.entries()).sort((f, d) => d[1] - f[1]).slice(0, 10);
      return new Map(c);
    }
    const r = [], o = /* @__PURE__ */ new Map();
    t.forEach((c) => {
      s(c.text || c).forEach((d) => {
        r.push(d), o.set(d, (o.get(d) || 0) + 1);
      });
    });
    const l = /* @__PURE__ */ new Map(), h = i.length, a = r.length, p = h + a;
    return (/* @__PURE__ */ new Set([...i, ...r])).forEach((c) => {
      const f = n.get(c) || 0, d = o.get(c) || 0;
      if (f === 0)
        return;
      const m = (f + d) * (h / p), v = (f + d) * (a / p);
      let u = 0;
      f > 0 && m > 0 && (u += 2 * f * Math.log(f / m)), d > 0 && v > 0 && (u += 2 * d * Math.log(d / v)), u > 0.01 && f > m && l.set(c, u);
    }), l;
  }
  /**
   * Get word-level importance scores for highlighting
   * Uses log-likelihood keyness to identify words unusually frequent in this chunk
   * @param {string} chunkText - The chunk text
   * @param {Array} allChunks - All chunks for comparison
   * @returns {Map<string, number>} Word to keyness score
   */
  getWordImportanceScores(e, t = []) {
    return this.calculateKeyness(e, t);
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
  async findChunkTextPositions(e, t, s, i = []) {
    const n = await this.findChunkTextPositionsExact(e, t, s);
    if (n.length > 0) {
      const r = this.getWordImportanceScores(t, i);
      return n.forEach((o) => {
        o.wordScores = r;
      }), n;
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
  async findChunkTextPositionsExact(e, t, s) {
    try {
      const i = await e.getTextContent();
      if (!i || !i.items || i.items.length === 0)
        return console.warn("No text content found on page"), [];
      const n = (g) => g.toLowerCase().trim().replace(/\s+/g, " "), r = n(t);
      if (!r || r.length < 10)
        return console.warn("Chunk text too short for reliable matching"), [];
      const o = i.items, l = o.map((g) => g.str).join(" "), h = n(l);
      let a = h.indexOf(r), p = r;
      if (a === -1) {
        const g = r.split(" "), c = g.slice(0, Math.min(20, g.length)).join(" ");
        a = h.indexOf(c), a !== -1 && (p = c);
      }
      if (a === -1) {
        const g = r.split(" "), c = g.slice(0, Math.min(10, g.length)).join(" ");
        a = h.indexOf(c), a !== -1 && (p = c);
      }
      return a === -1 ? (console.warn(`Chunk text not found on page: "${t.substring(0, 50)}..."`), []) : this.findTextItemPositions(o, p, a, h, s, n);
    } catch (i) {
      return console.error("Error finding chunk text positions:", i), [];
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
  findTextItemPositions(e, t, s, i, n, r) {
    const o = [];
    let l = 0;
    const h = [];
    for (let a = 0; a < e.length; a++) {
      const p = e[a], g = r(p.str), c = g.length + 1;
      if (l + g.length >= s && l <= s + t.length && h.push(p), l += c, l > s + t.length)
        break;
    }
    if (h.length === 0) {
      const a = t.split(" ").slice(0, 5).join(" ");
      let p = "";
      for (const g of e) {
        const c = r(g.str);
        if (p += c + " ", h.push(g), r(p).includes(a))
          break;
        if (h.length > 50) {
          h.length = 0;
          break;
        }
      }
    }
    if (h.length > 0) {
      const a = this.calculateBoundingBox(h, n);
      a && a.width > 0 && a.height > 0 && o.push(a);
    }
    return o;
  }
  /**
   * Calculate bounding box from text items and convert to viewport coordinates
   * @param {Array} textItems - Array of text items that form the match
   * @param {Object} viewport - PDF.js viewport object
   * @returns {Object|null} Bounding box {x, y, width, height} in viewport coordinates, or null
   */
  calculateBoundingBox(e, t) {
    if (!e || e.length === 0)
      return null;
    let s = 1 / 0, i = 1 / 0, n = -1 / 0, r = -1 / 0;
    for (const d of e)
      if (d.transform && d.transform.length >= 6) {
        const m = d.transform[4], v = d.transform[5], u = d.width || 0, y = d.height || Math.abs(d.transform[3]) || 12;
        s = Math.min(s, m), i = Math.min(i, v), n = Math.max(n, m + u), r = Math.max(r, v + y);
      } else if (d.x !== void 0 && d.y !== void 0) {
        const m = d.x, v = d.y, u = d.width || 0, y = d.height || 12;
        s = Math.min(s, m), i = Math.min(i, v), n = Math.max(n, m + u), r = Math.max(r, v + y);
      }
    if (s === 1 / 0 || i === 1 / 0)
      return null;
    let o, l, h, a;
    if (t.convertToViewportPoint)
      [o, l] = t.convertToViewportPoint(s, i), [h, a] = t.convertToViewportPoint(n, r);
    else {
      const d = t.height / t.scale;
      o = s * t.scale, l = (d - r) * t.scale, h = n * t.scale, a = (d - i) * t.scale;
    }
    const p = Math.min(o, h), g = Math.min(l, a), c = Math.abs(h - o), f = Math.abs(a - l);
    return c < 1 || f < 1 ? null : { x: p, y: g, width: c, height: f };
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
  async addWordLevelHighlights(e, t, s, i, n, r) {
    try {
      const o = await t.getTextContent();
      if (!o || !o.items)
        return;
      const l = /* @__PURE__ */ new Set([
        "the",
        "be",
        "to",
        "of",
        "and",
        "a",
        "in",
        "that",
        "have",
        "i",
        "it",
        "for",
        "not",
        "on",
        "with",
        "he",
        "as",
        "you",
        "do",
        "at",
        "this",
        "but",
        "his",
        "by",
        "from",
        "they",
        "we",
        "say",
        "her",
        "she",
        "or",
        "an",
        "will",
        "my",
        "one",
        "all",
        "would",
        "there",
        "their",
        "what",
        "so",
        "up",
        "out",
        "if",
        "about",
        "who",
        "get",
        "which",
        "go",
        "me",
        "when",
        "make",
        "can",
        "like",
        "time",
        "no",
        "just",
        "him",
        "know",
        "take",
        "people",
        "into",
        "year",
        "your",
        "good",
        "some",
        "could",
        "them",
        "see",
        "other",
        "than",
        "then",
        "now",
        "look",
        "only",
        "come",
        "its",
        "over",
        "think",
        "also",
        "back",
        "after",
        "use",
        "two",
        "how",
        "our",
        "work",
        "first",
        "well",
        "way",
        "even",
        "new",
        "want",
        "because",
        "any",
        "these",
        "give",
        "day",
        "most",
        "us",
        "is",
        "are",
        "was",
        "were",
        "been",
        "being",
        "has",
        "had",
        "does",
        "did",
        "may",
        "might",
        "must",
        "shall",
        "should",
        "could",
        "would",
        "can",
        "cannot",
        "will",
        "shall"
      ]);
      let h = i;
      i instanceof Map || (h = new Map(Object.entries(i || {})));
      const a = Array.from(h.entries()).sort((w, x) => x[1] - w[1]).slice(0, 10);
      if (a.length === 0) {
        console.warn("No key words found for highlighting - keyness scores may be empty. WordScores:", h);
        return;
      }
      console.log(`Found ${a.length} key words for highlighting:`, a.map(([w, x]) => `${w}(${x.toFixed(3)})`));
      const p = a[0][1], g = a[a.length - 1][1], c = p - g || 1, f = (w) => w.toLowerCase().replace(/[^\w]/g, ""), d = /* @__PURE__ */ new Set(), m = /* @__PURE__ */ new Map();
      if (a.forEach(([w, x]) => {
        const k = f(w);
        k.length >= 3 && (d.add(k), m.set(k, x));
      }), d.size === 0)
        return;
      const v = 0.1, u = s.x - s.width * v, y = s.x + s.width + s.width * v, T = s.y - s.height * v, j = s.y + s.height + s.height * v, D = n.height / n.scale, O = (w, x, k, C) => {
        if (n.convertToViewportPoint) {
          const [L, q] = n.convertToViewportPoint(w, x), W = w + k, E = x + C, [P, I] = n.convertToViewportPoint(W, E);
          return {
            x: L,
            y: q,
            width: Math.abs(P - L),
            height: Math.abs(I - q)
          };
        } else
          return {
            x: w * n.scale,
            y: (D - (x + C)) * n.scale,
            width: k * n.scale,
            height: C * n.scale
          };
      };
      let S = 0;
      const N = 50;
      for (const w of o.items) {
        if (S >= N) break;
        if (!w.transform || w.transform.length < 6) continue;
        const x = w.transform[4], k = w.transform[5], C = w.width || 0, L = w.height || Math.abs(w.transform[3]) || 12, q = x + C, W = k + L, E = O(x, k, C, L), P = E.x, I = E.y, F = E.width, R = E.height;
        if (P < u || P + F > y || I < T || I + R > j)
          continue;
        const M = f(w.str);
        if (d.has(M)) {
          const $ = m.get(M), z = 0.5 + ($ - g) / c * 0.4, _ = document.createElement("div");
          _.className = `word-highlight ${r ? "evidence-word" : ""}`, _.style.left = `${P / n.width * 100}%`, _.style.top = `${I / n.height * 100}%`, _.style.width = `${F / n.width * 100}%`, _.style.height = `${R / n.height * 100}%`, _.style.opacity = z, _.style.backgroundColor = r ? "rgba(255, 200, 0, 0.7)" : "rgba(255, 255, 0, 0.6)", _.style.borderRadius = "2px", _.title = `Important word: "${w.str}" (Keyness: ${$.toFixed(3)})`, e.appendChild(_), S++;
        } else
          for (const $ of d)
            if (M.startsWith($) || M.endsWith($)) {
              const A = m.get($), _ = 0.5 + (A - g) / c * 0.4, b = document.createElement("div");
              b.className = `word-highlight ${r ? "evidence-word" : ""}`, b.style.left = `${P / n.width * 100}%`, b.style.top = `${I / n.height * 100}%`, b.style.width = `${F / n.width * 100}%`, b.style.height = `${R / n.height * 100}%`, b.style.opacity = _, b.style.backgroundColor = r ? "rgba(255, 200, 0, 0.7)" : "rgba(255, 255, 0, 0.6)", b.style.borderRadius = "2px", b.title = `Important word: "${w.str}" (Keyness: ${A.toFixed(3)})`, e.appendChild(b), S++;
              break;
            }
      }
      console.log(`Added ${S} word highlights for ${a.length} key words`);
    } catch (o) {
      console.error("Error adding word-level highlights:", o);
    }
  }
  async navigateToPage(e) {
    const t = this._selectedQuestionId, s = this._showEvidenceOnly;
    this._currentPage = e, await this.render(), this._selectedQuestionId = t, this._showEvidenceOnly = s, requestAnimationFrame(() => {
      var r, o;
      const i = (r = this.shadowRoot) == null ? void 0 : r.getElementById("question-select");
      i && (i.value = t || "");
      const n = (o = this.shadowRoot) == null ? void 0 : o.getElementById("evidence-filter");
      n && (n.checked = s);
    });
  }
  async navigateToChunk(e) {
    const t = this._selectedQuestionId, s = this._showEvidenceOnly;
    let i = 1;
    if (e.metadata && (e.metadata.page_number !== void 0 ? i = parseInt(e.metadata.page_number) || 1 : e.metadata.source !== void 0 && (i = parseInt(e.metadata.source) || 1)), this._pdfDoc) {
      const n = this._pdfDoc.numPages;
      i < 1 && (i = 1), i > n && (i = n);
    }
    await this.navigateToPage(i), this._selectedQuestionId = t, this._showEvidenceOnly = s, this.dispatchEvent(new CustomEvent("chunk-selected", {
      detail: { chunk: e, pageNum: i },
      bubbles: !0,
      composed: !0
    }));
  }
  // Public API: Navigate to chunk by ID (for Streamlit communication)
  // chunkId format: "question_id_chunk_order" (e.g., "tcfd_1_0")
  // Note: question_id may contain underscores, so we split from the right
  async navigateToChunkById(e) {
    if (!e) return;
    const t = e.lastIndexOf("_");
    if (t === -1) {
      console.warn(`Invalid chunk ID format: ${e}. Expected format: "question_id_chunk_order"`);
      return;
    }
    const s = e.substring(0, t), i = e.substring(t + 1), n = parseInt(i);
    if (isNaN(n)) {
      console.warn(`Invalid chunk order in chunk ID: ${e} (parsed as: ${i})`);
      return;
    }
    const r = this._chunks.find((l) => {
      const h = l.question_id || "", a = l.chunk_order !== void 0 ? l.chunk_order : -1;
      return h === s && (a === n || a === n - 1 || a === n + 1);
    });
    if (!r) {
      console.warn(`Chunk not found for ID: ${e} (question_id: ${s}, chunk_order: ${n})`), console.debug("Available chunks:", this._chunks.map((l) => ({
        question_id: l.question_id,
        chunk_order: l.chunk_order
      })));
      return;
    }
    const o = this._showEvidenceOnly;
    this.setSelectedQuestionId(s), await new Promise((l) => setTimeout(l, 100)), await this.navigateToChunk(r), this._showEvidenceOnly = o, this._highlightedChunkId = e;
  }
  async render() {
    if (!this.shadowRoot) return;
    const e = this._selectedQuestionId, t = this._showEvidenceOnly, s = this.getFilteredChunks(), i = {};
    s.forEach((o) => {
      let l = 1;
      o.metadata && (o.metadata.page_number !== void 0 ? l = parseInt(o.metadata.page_number) || 1 : o.metadata.source !== void 0 && (l = parseInt(o.metadata.source) || 1)), i[l] || (i[l] = []), i[l].push(o);
    });
    const n = `
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
    `, r = `
      <div class="container">
        <div class="sidebar">
          <div class="sidebar-header">
            <h3>Chunks by Question</h3>
            <div class="question-selector">
              <select id="question-select">
                <option value="">All Questions</option>
                ${this._questions.map((o) => `
                  <option value="${o.question_id}" ${this._selectedQuestionId === o.question_id ? "selected" : ""}>
                    ${o.text ? o.text.substring(0, 50) + "..." : o.question_id}
                  </option>
                `).join("")}
              </select>
            </div>
            <div class="evidence-filter">
              <input type="checkbox" id="evidence-filter" ${this._showEvidenceOnly ? "checked" : ""}>
              <label for="evidence-filter">Show evidence only</label>
            </div>
          </div>
          <div class="chunks-list">
            ${s.length === 0 ? '<div style="padding: 16px; color: #999; text-align: center;">No chunks to display</div>' : ""}
            ${s.map((o, l) => {
      var d, m;
      let h = "?";
      o.metadata && (o.metadata.page_number !== void 0 ? h = parseInt(o.metadata.page_number) || "?" : o.metadata.source !== void 0 && (h = parseInt(o.metadata.source) || "?"));
      const a = o.is_evidence === !0, p = ((d = o.similarity_score) == null ? void 0 : d.toFixed(3)) || "N/A", g = ((m = o.llm_score) == null ? void 0 : m.toFixed(3)) || "N/A", c = o.text || "", f = c.substring(0, 150) + (c.length > 150 ? "..." : "");
      return `
                <div class="chunk-item ${a ? "evidence" : ""}" data-chunk-index="${l}">
                  <div class="chunk-header">
                    <span class="chunk-title">Chunk ${o.chunk_order !== void 0 ? o.chunk_order + 1 : l + 1}</span>
                    <div style="display: flex; gap: 4px;">
                      ${a ? '<span class="chunk-badge evidence">Evidence</span>' : ""}
                      <span class="chunk-badge page">Page ${h}</span>
                    </div>
                  </div>
                  <div class="chunk-text">${this.escapeHtml(f)}</div>
                  <div class="chunk-scores">
                    <span>Similarity: ${p}</span>
                    ${o.llm_score !== null && o.llm_score !== void 0 ? `<span>LLM: ${g}</span>` : ""}
                  </div>
                </div>
              `;
    }).join("")}
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
    this.shadowRoot.innerHTML = n + r, this._selectedQuestionId = e, this._showEvidenceOnly = t, this.setupEventListeners(), setTimeout(() => {
      const o = this.shadowRoot.getElementById("question-select");
      o && this._selectedQuestionId !== void 0 && (o.value = this._selectedQuestionId || "");
      const l = this.shadowRoot.getElementById("evidence-filter");
      l && this._showEvidenceOnly !== void 0 && (l.checked = this._showEvidenceOnly);
    }, 0), this.loadAndRenderPdf();
  }
  escapeHtml(e) {
    const t = document.createElement("div");
    return t.textContent = e, t.innerHTML;
  }
  setupEventListeners() {
    const e = this.shadowRoot.getElementById("question-select");
    e && e.addEventListener("change", (n) => {
      this.setSelectedQuestionId(n.target.value || null, !0);
    });
    const t = this.shadowRoot.getElementById("evidence-filter");
    t && t.addEventListener("change", (n) => {
      this.setShowEvidenceOnly(n.target.checked, !0);
    }), this.attachChunkListeners();
    const s = this.shadowRoot.getElementById("prev-page"), i = this.shadowRoot.getElementById("next-page");
    s && s.addEventListener("click", () => {
      this._currentPage > 1 && this.navigateToPage(this._currentPage - 1);
    }), i && i.addEventListener("click", async () => {
      if (this._pdfDoc) {
        const n = this._pdfDoc.numPages;
        this._currentPage < n && await this.navigateToPage(this._currentPage + 1);
      }
    });
  }
  async loadAndRenderPdf() {
    try {
      this._isLoading = !0, this.updateLoadingDisplay();
      const t = (await this.loadPdf()).numPages, s = this.shadowRoot.getElementById("total-pages");
      s && (s.textContent = t), await this.renderCurrentPage(), this._isLoading = !1;
    } catch (e) {
      this._isLoading = !1;
      const t = this.shadowRoot.getElementById("viewer-content");
      t && (t.innerHTML = `<div class="error">Error loading PDF: ${e.message}</div>`);
    }
  }
  async renderCurrentPage() {
    const e = this.shadowRoot.getElementById("viewer-content");
    if (e)
      try {
        const t = await this.loadPdf(), s = t.numPages;
        this._currentPage < 1 && (this._currentPage = 1), this._currentPage > s && (this._currentPage = s);
        const i = this.shadowRoot.getElementById("current-page");
        i && (i.textContent = this._currentPage);
        const n = await this.renderPage(this._currentPage);
        if (!n) {
          e.innerHTML = '<div class="error">Error rendering page</div>';
          return;
        }
        const r = await t.getPage(this._currentPage), o = r.getViewport({ scale: this._scale }), l = this.getFilteredChunks(), h = l.filter((c) => {
          let f = 1;
          return c.metadata && (c.metadata.page_number !== void 0 ? f = parseInt(c.metadata.page_number) || 1 : c.metadata.source !== void 0 && (f = parseInt(c.metadata.source) || 1)), f === this._currentPage;
        }), a = document.createElement("div");
        a.className = "page-container";
        const p = document.createElement("canvas");
        if (p.className = "page-canvas", p.width = n.width, p.height = n.height, p.getContext("2d").drawImage(n, 0, 0), a.appendChild(p), h.length > 0) {
          const c = document.createElement("div");
          c.className = "page-highlights";
          const f = l.map((d) => ({ text: d.text || "" }));
          for (const d of h) {
            const m = d.text || "";
            if (!m || m.trim().length === 0)
              continue;
            const v = await this.findChunkTextPositions(
              r,
              m,
              o,
              f
            );
            if (v.length > 0)
              v.forEach((u) => {
                const y = document.createElement("div");
                y.className = `highlight ${d.is_evidence === !0 || d.is_evidence === 1 ? "evidence" : ""}`;
                const T = u.x / o.width * 100, j = u.y / o.height * 100, D = u.width / o.width * 100, O = u.height / o.height * 100;
                y.style.left = `${T}%`, y.style.top = `${j}%`, y.style.width = `${D}%`, y.style.height = `${O}%`, y.title = d.is_evidence === !0 || d.is_evidence === 1 ? `Evidence chunk: ${m.substring(0, 50)}...` : `Chunk: ${m.substring(0, 50)}...`, c.appendChild(y), u.wordScores && (u.wordScores instanceof Map ? u.wordScores.size > 0 : Object.keys(u.wordScores || {}).length > 0) ? (console.log(`Adding word highlights for chunk with ${u.wordScores instanceof Map ? u.wordScores.size : Object.keys(u.wordScores || {}).length} word scores`), this.addWordLevelHighlights(
                  c,
                  r,
                  u,
                  u.wordScores,
                  o,
                  d.is_evidence === !0 || d.is_evidence === 1
                )) : console.warn("No wordScores found for chunk, skipping word highlights");
              });
            else {
              console.warn(`Could not find text position for chunk on page ${this._currentPage}`);
              const u = document.createElement("div");
              u.className = `highlight ${d.is_evidence === !0 || d.is_evidence === 1 ? "evidence" : ""}`, u.style.top = "5%", u.style.left = "5%", u.style.width = "10px", u.style.height = "10px", u.style.borderRadius = "50%", u.title = "Chunk text position not found", c.appendChild(u);
            }
          }
          a.appendChild(c);
        }
        e.innerHTML = "", e.appendChild(a);
      } catch (t) {
        console.error("Error rendering current page:", t), e.innerHTML = `<div class="error">Error rendering page: ${t.message}</div>`;
      }
  }
}
customElements.get("pdf-viewer-with-chunks") || customElements.define("pdf-viewer-with-chunks", B);
export {
  B as default
};
