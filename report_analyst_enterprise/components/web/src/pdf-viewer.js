import "./pdfjs-map-polyfill.js";
import * as pdfjsLib from "pdfjs-dist/build/pdf.mjs";

pdfjsLib.GlobalWorkerOptions.workerSrc = "./pdf-worker-bootstrap.mjs";

const MIN_MATCH_TOKENS = 6;
const UNMAPPED_QUESTION_ID = "__unmapped__";

const STYLES = `
  <style>
    :host {
      display: block;
      height: 100vh;
      font-family: system-ui, sans-serif;
    }
    .container {
      display: flex;
      width: 100%;
      height: 100%;
      min-width: 0;
      background: #f5f5f5;
    }
    .sidebar {
      display: flex;
      flex: 0 0 clamp(220px, 32%, 350px);
      flex-direction: column;
      min-width: 0;
      overflow: hidden;
      background: white;
      border-right: 1px solid #e0e0e0;
    }
    .sidebar-header {
      padding: 16px;
      background: #fafafa;
      border-bottom: 1px solid #e0e0e0;
    }
    .sidebar-header h3 {
      margin: 0 0 12px;
      font-size: 16px;
    }
    .question-select {
      width: 100%;
      margin-bottom: 12px;
      padding: 8px;
    }
    .evidence-filter {
      display: flex;
      align-items: center;
      gap: 8px;
      color: #666;
      font-size: 14px;
    }
    .chunks-list {
      flex: 1;
      overflow-y: auto;
      padding: 8px;
    }
    .empty {
      padding: 16px;
      color: #777;
      text-align: center;
    }
    .chunk-item {
      margin-bottom: 8px;
      padding: 12px;
      background: white;
      border: 1px solid #e0e0e0;
      border-radius: 6px;
      cursor: pointer;
    }
    .chunk-item:hover {
      border-color: #4313c8;
      box-shadow: 0 2px 4px rgba(67, 19, 200, 0.1);
    }
    .chunk-item.evidence {
      background: #f8f7ff;
      border-left: 4px solid #4313c8;
    }
    .chunk-header,
    .badges,
    .chunk-scores {
      display: flex;
      align-items: center;
    }
    .chunk-header {
      justify-content: space-between;
      margin-bottom: 8px;
    }
    .chunk-title {
      color: #333;
      font-size: 14px;
      font-weight: 600;
    }
    .badges {
      gap: 4px;
    }
    .badge {
      padding: 2px 8px;
      border-radius: 12px;
      background: #e0e0e0;
      color: #666;
      font-size: 11px;
      font-weight: 600;
    }
    .badge.evidence {
      background: #4313c8;
      color: white;
    }
    .chunk-text {
      display: -webkit-box;
      overflow: hidden;
      color: #666;
      font-size: 13px;
      line-height: 1.5;
      -webkit-box-orient: vertical;
      -webkit-line-clamp: 3;
    }
    .chunk-scores {
      gap: 12px;
      margin-top: 8px;
      color: #888;
      font-size: 11px;
    }
    .viewer {
      display: flex;
      flex: 1;
      flex-direction: column;
      min-width: 0;
      overflow: hidden;
      background: #525252;
    }
    .viewer-controls {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 12px 16px;
      background: white;
      border-bottom: 1px solid #e0e0e0;
    }
    .viewer-controls button {
      padding: 6px 12px;
      background: white;
      border: 1px solid #ddd;
      border-radius: 4px;
      cursor: pointer;
    }
    .viewer-controls button:disabled {
      cursor: default;
      opacity: 0.45;
    }
    .page-info {
      color: #666;
      font-size: 14px;
    }
    .viewer-content {
      display: flex;
      flex: 1;
      align-items: flex-start;
      justify-content: center;
      overflow: auto;
      padding: 20px;
    }
    .page-container {
      position: relative;
      flex: none;
      background: white;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
    }
    .page-canvas {
      display: block;
    }
    .page-highlights {
      position: absolute;
      inset: 0;
      pointer-events: none;
    }
    .highlight {
      position: absolute;
      z-index: 1;
      background: transparent;
      border: 1px solid rgba(67, 19, 200, 0.35);
      border-radius: 2px;
      pointer-events: auto;
      transition: background-color 0.15s ease, border-color 0.15s ease;
    }
    .highlight:hover {
      background: rgba(67, 19, 200, 0.2);
      border-color: rgba(67, 19, 200, 0.75);
    }
    .highlight.evidence {
      border-color: #4313c8;
    }
    .highlight.evidence:hover {
      background: rgba(67, 19, 200, 0.3);
    }
    .message {
      margin: auto;
      color: #eee;
      font-size: 14px;
    }
    .message.error {
      color: #fecaca;
    }
  </style>
`;

function tokenize(value) {
  return String(value || "")
    .normalize("NFKC")
    .replace(/\u00ad/g, "")
    .toLowerCase()
    .match(/[\p{L}\p{N}]+/gu) || [];
}

class PdfViewerWithChunks extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._pdfData = null;
    this._pdfDoc = null;
    this._loadingTask = null;
    this._chunks = [];
    this._questions = [];
    this._selectedQuestionId = null;
    this._showEvidenceOnly = false;
    this._currentPage = 1;
    this._renderId = 0;
    this._lastRenderedWidth = 0;
    this._resizeObserver = null;
  }

  connectedCallback() {
    this.render();
    this.observeViewerSize();
  }

  disconnectedCallback() {
    this._resizeObserver?.disconnect();
    this._resizeObserver = null;
    this.resetPdfDocument();
  }

  setPdfData(data) {
    if (data === this._pdfData) return;
    this.resetPdfDocument();
    this._pdfData = data || null;
    if (this.isConnected) void this.loadAndRenderPdf();
  }

  setChunks(chunks) {
    this._chunks = Array.isArray(chunks) ? chunks : [];
    if (
      this._selectedQuestionId === UNMAPPED_QUESTION_ID &&
      !this._chunks.some((chunk) => !chunk.question_id)
    ) {
      this._selectedQuestionId = null;
    }
    this.renderQuestionOptions();
    this.updateFilters();
  }

  setQuestions(questions) {
    this._questions = Array.isArray(questions) ? questions : [];
    if (
      this._selectedQuestionId &&
      this._selectedQuestionId !== UNMAPPED_QUESTION_ID &&
      !this._questions.some((question) => question.question_id === this._selectedQuestionId)
    ) {
      this._selectedQuestionId = null;
      this.updateFilters();
      return;
    }
    this.renderQuestionOptions();
  }

  setSelectedQuestionId(questionId) {
    const selected = questionId || null;
    if (selected === this._selectedQuestionId) return;
    this._selectedQuestionId = selected;
    this.updateFilters();
  }

  setShowEvidenceOnly(show) {
    const evidenceOnly = Boolean(show);
    if (evidenceOnly === this._showEvidenceOnly) return;
    this._showEvidenceOnly = evidenceOnly;
    this.updateFilters();
  }

  resetPdfDocument() {
    this._renderId += 1;
    void this._loadingTask?.destroy();
    this._loadingTask = null;
    if (this._pdfDoc) void this._pdfDoc.destroy();
    this._pdfDoc = null;
    this._currentPage = 1;
    this._lastRenderedWidth = 0;
  }

  observeViewerSize() {
    this._resizeObserver?.disconnect();
    if (typeof ResizeObserver !== "function") return;

    const content = this.shadowRoot?.getElementById("viewer-content");
    if (!content) return;

    this._resizeObserver = new ResizeObserver(() => {
      const width = content.clientWidth;
      if (
        !this._pdfDoc ||
        width <= 0 ||
        width === this._lastRenderedWidth
      ) {
        return;
      }
      void this.renderCurrentPage();
    });
    this._resizeObserver.observe(content);
  }

  render() {
    this.shadowRoot.innerHTML = `${STYLES}
      <div class="container">
        <aside class="sidebar">
          <div class="sidebar-header">
            <h3>Chunks by Question</h3>
            <select id="question-select" class="question-select"></select>
            <label class="evidence-filter">
              <input id="evidence-filter" type="checkbox">
              <span id="evidence-filter-label">Show evidence only</span>
            </label>
          </div>
          <div class="chunks-list"></div>
        </aside>
        <main class="viewer">
          <div class="viewer-controls">
            <button id="prev-page" type="button">Previous</button>
            <span class="page-info">
              Page <span id="current-page">1</span> of <span id="total-pages">-</span>
            </span>
            <button id="next-page" type="button">Next</button>
          </div>
          <div id="viewer-content" class="viewer-content"></div>
        </main>
      </div>
    `;

    this.bindEvents();
    this.renderQuestionOptions();
    this.updateFilters();
    this.updatePageControls();
  }

  bindEvents() {
    this.shadowRoot.getElementById("question-select").addEventListener("change", (event) => {
      this.setSelectedQuestionId(event.target.value);
    });
    this.shadowRoot.getElementById("evidence-filter").addEventListener("change", (event) => {
      this.setShowEvidenceOnly(event.target.checked);
    });
    this.shadowRoot.querySelector(".chunks-list").addEventListener("click", (event) => {
      const item = event.target instanceof Element
        ? event.target.closest(".chunk-item")
        : null;
      if (!item) return;
      const chunk = this.getFilteredChunks()[Number(item.dataset.chunkIndex)];
      if (chunk) void this.navigateToChunk(chunk);
    });
    this.shadowRoot.getElementById("prev-page").addEventListener("click", () => {
      void this.navigateToPage(this._currentPage - 1);
    });
    this.shadowRoot.getElementById("next-page").addEventListener("click", () => {
      void this.navigateToPage(this._currentPage + 1);
    });
  }

  renderQuestionOptions() {
    const select = this.shadowRoot?.getElementById("question-select");
    if (!select) return;

    select.replaceChildren(new Option("All Questions", ""));
    for (const question of this._questions) {
      const text = question.text || question.question_id;
      const status = this.getQuestionStatus(question.question_id);
      select.add(new Option(`${status} — ${text}`, question.question_id));
    }
    if (this._chunks.some((chunk) => !chunk.question_id)) {
      select.add(new Option("Unmapped chunks", UNMAPPED_QUESTION_ID));
    }
    select.value = this._selectedQuestionId || "";
  }

  updateFilters() {
    const select = this.shadowRoot?.getElementById("question-select");
    const checkbox = this.shadowRoot?.getElementById("evidence-filter");
    const evidenceLabel = this.shadowRoot?.getElementById("evidence-filter-label");
    const evidenceAvailable = this.getScopedChunks().some((chunk) =>
      this.hasEvidenceMapping(chunk)
    );
    if (!evidenceAvailable) this._showEvidenceOnly = false;
    if (select) select.value = this._selectedQuestionId || "";
    if (checkbox) {
      checkbox.checked = this._showEvidenceOnly;
      checkbox.disabled = !evidenceAvailable;
    }
    if (evidenceLabel) {
      evidenceLabel.textContent = evidenceAvailable
        ? "Show evidence only"
        : "Evidence unavailable";
    }
    this.renderChunkList();
    if (this._pdfDoc) void this.renderCurrentPage();
  }

  getScopedChunks() {
    let chunks = this._chunks;
    if (this._selectedQuestionId === UNMAPPED_QUESTION_ID) {
      chunks = chunks.filter((chunk) => !chunk.question_id);
    } else if (this._selectedQuestionId) {
      chunks = chunks.filter((chunk) => chunk.question_id === this._selectedQuestionId);
    }
    return chunks;
  }

  getFilteredChunks() {
    let chunks = this.getScopedChunks();
    if (this._showEvidenceOnly) {
      chunks = chunks.filter((chunk) => this.isEvidenceChunk(chunk));
    }
    return chunks;
  }

  renderChunkList() {
    const list = this.shadowRoot?.querySelector(".chunks-list");
    if (!list) return;

    const chunks = this.getFilteredChunks();
    if (!chunks.length) {
      list.innerHTML = '<div class="empty">No chunks to display</div>';
      return;
    }

    list.innerHTML = chunks.map((chunk, index) => {
      const evidence = this.isEvidenceChunk(chunk);
      const order = chunk.chunk_order == null ? index + 1 : Number(chunk.chunk_order) + 1;
      const page = this.getChunkPage(chunk) ?? "?";
      const text = String(chunk.text || "");
      const preview = text.length > 150 ? `${text.slice(0, 150)}...` : text;
      const status = this.getChunkStatus(chunk);
      let statusBadge = "";
      if (evidence) {
        statusBadge = '<span class="badge evidence">Evidence</span>';
      } else if (status !== "Analyzed") {
        statusBadge = `<span class="badge">${status}</span>`;
      }
      const llmScore = chunk.llm_score == null
        ? ""
        : `<span>LLM: ${this.formatScore(chunk.llm_score)}</span>`;

      return `
        <article class="chunk-item ${evidence ? "evidence" : ""}" data-chunk-index="${index}">
          <div class="chunk-header">
            <span class="chunk-title">Chunk ${order}</span>
            <span class="badges">
              ${statusBadge}
              <span class="badge">Page ${page}</span>
            </span>
          </div>
          <div class="chunk-text">${this.escapeHtml(preview)}</div>
          <div class="chunk-scores">
            <span>Similarity: ${this.formatScore(chunk.similarity_score)}</span>
            ${llmScore}
          </div>
        </article>
      `;
    }).join("");
  }

  async loadPdf() {
    if (this._pdfDoc) return this._pdfDoc;
    if (this._loadingTask) return this._loadingTask.promise;

    if (!this._pdfData) throw new Error("No PDF data provided");
    const encoded = this._pdfData.replace(/^data:application\/pdf;base64,/, "");
    const source = {
      data: Uint8Array.from(atob(encoded), (char) => char.charCodeAt(0)),
    };

    this._loadingTask = pdfjsLib.getDocument(source);
    try {
      this._pdfDoc = await this._loadingTask.promise;
      return this._pdfDoc;
    } finally {
      this._loadingTask = null;
    }
  }

  async loadAndRenderPdf() {
    this.showMessage("Loading PDF...");
    try {
      await this.loadPdf();
      this.updatePageControls();
      await this.renderCurrentPage();
    } catch (error) {
      this.showMessage(`Error loading PDF: ${error.message}`, "error");
    }
  }

  async navigateToPage(pageNumber) {
    const pdf = await this.loadPdf();
    this._currentPage = Math.min(Math.max(Number(pageNumber) || 1, 1), pdf.numPages);
    this.updatePageControls();
    await this.renderCurrentPage();
  }

  async navigateToChunk(chunk) {
    await this.navigateToPage(this.getChunkPage(chunk) ?? 1);
  }

  updatePageControls() {
    const total = this._pdfDoc?.numPages;
    const current = this.shadowRoot?.getElementById("current-page");
    const totalElement = this.shadowRoot?.getElementById("total-pages");
    const previous = this.shadowRoot?.getElementById("prev-page");
    const next = this.shadowRoot?.getElementById("next-page");

    if (current) current.textContent = String(this._currentPage);
    if (totalElement) totalElement.textContent = total ? String(total) : "-";
    if (previous) previous.disabled = this._currentPage <= 1;
    if (next) next.disabled = !total || this._currentPage >= total;
  }

  async renderCurrentPage() {
    const content = this.shadowRoot?.getElementById("viewer-content");
    if (!content) return;

    const renderId = ++this._renderId;
    try {
      const pdf = await this.loadPdf();
      const pageNumber = Math.min(Math.max(this._currentPage, 1), pdf.numPages);
      const page = await pdf.getPage(pageNumber);
      const baseViewport = page.getViewport({ scale: 1 });
      const containerWidth = content.clientWidth;
      this._lastRenderedWidth = containerWidth;
      const scale = this.getFitScale(baseViewport.width, containerWidth);
      const viewport = page.getViewport({ scale });
      const canvas = await this.renderPage(page, viewport);
      const textItems = await this.readTextItems(page);
      if (renderId !== this._renderId) return;

      this._currentPage = pageNumber;
      this.updatePageControls();

      const pageContainer = document.createElement("div");
      pageContainer.className = "page-container";
      pageContainer.append(canvas);

      const highlights = this.renderHighlights(textItems, viewport, pageNumber);
      if (highlights.childElementCount) pageContainer.append(highlights);
      content.replaceChildren(pageContainer);
    } catch (error) {
      if (renderId === this._renderId) {
        this.showMessage(`Error rendering page: ${error.message}`, "error");
      }
    }
  }

  async renderPage(page, viewport) {
    const outputScale = Math.max(1, window.devicePixelRatio || 1);
    const canvas = document.createElement("canvas");
    const context = canvas.getContext("2d");
    if (!context) throw new Error("Canvas is unavailable");

    canvas.className = "page-canvas";
    canvas.width = Math.floor(viewport.width * outputScale);
    canvas.height = Math.floor(viewport.height * outputScale);
    canvas.style.width = `${viewport.width}px`;
    canvas.style.height = `${viewport.height}px`;

    const renderContext = { canvasContext: context, viewport };
    if (outputScale !== 1) {
      renderContext.transform = [outputScale, 0, 0, outputScale, 0, 0];
    }
    await page.render(renderContext).promise;
    return canvas;
  }

  async readTextItems(page) {
    const reader = page.streamTextContent().getReader();
    const items = [];
    try {
      while (true) {
        const { value, done } = await reader.read();
        if (done) return items;
        items.push(...value.items);
      }
    } finally {
      reader.releaseLock();
    }
  }

  renderHighlights(textItems, viewport, pageNumber) {
    const layer = document.createElement("div");
    layer.className = "page-highlights";

    const chunks = this.getFilteredChunks().filter(
      (chunk) => this.getChunkPage(chunk) === pageNumber,
    );

    for (const chunk of chunks) {
      const boxes = this.findChunkTextPositions(textItems, chunk.text, viewport);
      for (const box of boxes) {
        const highlight = document.createElement("div");
        highlight.className = `highlight ${this.isEvidenceChunk(chunk) ? "evidence" : ""}`;
        highlight.style.left = `${(box.x / viewport.width) * 100}%`;
        highlight.style.top = `${(box.y / viewport.height) * 100}%`;
        highlight.style.width = `${(box.width / viewport.width) * 100}%`;
        highlight.style.height = `${(box.height / viewport.height) * 100}%`;
        highlight.title = this.getChunkTooltip(chunk);
        layer.append(highlight);
      }
    }
    return layer;
  }

  findChunkTextPositions(textItems, chunkText, viewport) {
    const chunkTokens = tokenize(chunkText);
    if (chunkTokens.length < MIN_MATCH_TOKENS) return [];

    const pageTokens = textItems.flatMap((item, itemIndex) =>
      tokenize(item.str).map((token) => ({ token, itemIndex })),
    );
    const ranges = this.findMatchingTokenRanges(
      pageTokens.map(({ token }) => token),
      chunkTokens,
    );
    const itemIndexes = new Set();
    for (const range of ranges) {
      for (let index = range.start; index <= range.end; index += 1) {
        itemIndexes.add(pageTokens[index].itemIndex);
      }
    }
    const matchingItems = textItems.flatMap((item, index) =>
      itemIndexes.has(index) ? [{ item, index }] : [],
    );

    return this.groupTextLines(matchingItems)
      .map((line) => this.calculateBoundingBox(line, viewport))
      .filter(Boolean);
  }

  findMatchingTokenRanges(pageTokens, chunkTokens) {
    const ranges = [];
    let previous = new Uint16Array(chunkTokens.length + 1);

    for (let pageIndex = 0; pageIndex < pageTokens.length; pageIndex += 1) {
      const current = new Uint16Array(chunkTokens.length + 1);
      for (let chunkIndex = 0; chunkIndex < chunkTokens.length; chunkIndex += 1) {
        if (pageTokens[pageIndex] !== chunkTokens[chunkIndex]) continue;

        const length = previous[chunkIndex] + 1;
        current[chunkIndex + 1] = length;
        const continues = pageIndex + 1 < pageTokens.length &&
          chunkIndex + 1 < chunkTokens.length &&
          pageTokens[pageIndex + 1] === chunkTokens[chunkIndex + 1];
        if (length >= MIN_MATCH_TOKENS && !continues) {
          ranges.push({
            start: pageIndex - length + 1,
            end: pageIndex,
            length,
          });
        }
      }
      previous = current;
    }

    const nonOverlappingRanges = [];
    for (const range of ranges.sort((a, b) => b.length - a.length)) {
      const overlaps = nonOverlappingRanges.some(
        (match) => range.start <= match.end && range.end >= match.start,
      );
      if (!overlaps) nonOverlappingRanges.push(range);
    }
    return nonOverlappingRanges.sort((a, b) => a.start - b.start);
  }

  groupTextLines(entries) {
    const lines = [];
    for (const { item, index } of entries) {
      const baseline = item.transform[5];
      const height = item.height || Math.abs(item.transform[3]);

      const line = lines.at(-1);
      const tolerance = line ? Math.max(2, Math.min(line.height, height) * 0.5) : 0;
      if (
        line &&
        index === line.lastIndex + 1 &&
        Math.abs(line.baseline - baseline) <= tolerance
      ) {
        line.items.push(item);
        line.lastIndex = index;
      } else {
        lines.push({ baseline, height, lastIndex: index, items: [item] });
      }
    }
    return lines.map((line) => line.items);
  }

  calculateBoundingBox(items, viewport) {
    let minX = Infinity;
    let minY = Infinity;
    let maxX = -Infinity;
    let maxY = -Infinity;

    for (const item of items) {
      const x = item.transform[4];
      const y = item.transform[5];
      const width = item.width;
      const height = item.height || Math.abs(item.transform[3]);
      minX = Math.min(minX, x);
      minY = Math.min(minY, y);
      maxX = Math.max(maxX, x + width);
      maxY = Math.max(maxY, y + height);
    }
    const firstCorner = viewport.convertToViewportPoint(minX, minY);
    const oppositeCorner = viewport.convertToViewportPoint(maxX, maxY);

    const width = Math.abs(oppositeCorner[0] - firstCorner[0]);
    const height = Math.abs(oppositeCorner[1] - firstCorner[1]);
    if (width < 1 || height < 1) return null;
    return {
      x: Math.min(firstCorner[0], oppositeCorner[0]),
      y: Math.min(firstCorner[1], oppositeCorner[1]),
      width,
      height,
    };
  }

  getChunkPage(chunk) {
    const value = chunk.metadata?.page_number ?? chunk.metadata?.source;
    const page = Number.parseInt(value, 10);
    return Number.isInteger(page) && page > 0 ? page : null;
  }

  isEvidenceChunk(chunk) {
    return chunk.is_evidence === true || chunk.is_evidence === 1;
  }

  hasEvidenceMapping(chunk) {
    return Object.hasOwn(chunk, "is_evidence") && chunk.is_evidence != null;
  }

  getChunkStatus(chunk) {
    if (!chunk.question_id) return "Unmapped";
    return this.hasEvidenceMapping(chunk) ? "Analyzed" : "Mapped";
  }

  getQuestionStatus(questionId) {
    const chunks = this._chunks.filter((chunk) => chunk.question_id === questionId);
    if (!chunks.length) return "Not mapped";
    return chunks.some((chunk) => this.hasEvidenceMapping(chunk))
      ? "Analyzed"
      : "Mapped";
  }

  getFitScale(pageWidth, containerWidth) {
    if (pageWidth <= 0 || containerWidth <= 0) return 1;
    return Math.max(0.1, (containerWidth - 40) / pageWidth);
  }

  formatScore(score) {
    const value = Number(score);
    return Number.isFinite(value) ? value.toFixed(3) : "N/A";
  }

  getChunkTooltip(chunk) {
    let chunkType = `${this.getChunkStatus(chunk)} chunk`;
    if (this.isEvidenceChunk(chunk)) chunkType = "Evidence";
    else if (this.hasEvidenceMapping(chunk)) chunkType = "Retrieved chunk";
    const order = chunk.chunk_order == null ? "N/A" : Number(chunk.chunk_order) + 1;
    return [
      chunkType,
      `Similarity: ${this.formatScore(chunk.similarity_score)}`,
      `LLM: ${this.formatScore(chunk.llm_score)}`,
      `Chunk order: ${order}`,
    ].join(" | ");
  }

  showMessage(message, className = "") {
    const content = this.shadowRoot?.getElementById("viewer-content");
    if (!content) return;
    const messageElement = document.createElement("div");
    messageElement.className = `message ${className}`.trim();
    messageElement.textContent = message;
    content.replaceChildren(messageElement);
  }

  escapeHtml(value) {
    const element = document.createElement("div");
    element.textContent = String(value ?? "");
    return element.innerHTML;
  }
}

if (!customElements.get("pdf-viewer-with-chunks")) {
  customElements.define("pdf-viewer-with-chunks", PdfViewerWithChunks);
}

export default PdfViewerWithChunks;
