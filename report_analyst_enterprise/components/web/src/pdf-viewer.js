import "./pdfjs-map-polyfill.js";
import styleText from "./pdf-viewer.styles.js";
import * as pdfjsLib from "pdfjs-dist/build/pdf.mjs";

pdfjsLib.GlobalWorkerOptions.workerSrc = "./pdf-worker-bootstrap.mjs";

const MIN_MATCH_TOKENS = 6;
const UNMAPPED_QUESTION_ID = "__unmapped__";
const TEXT_ITEM = "[data-source-text-start]";
// From this version Chromium keeps a selection steady across blank space by itself.
const NATIVE_SELECTION_CHROMIUM = 148;

const STYLES = `<style>${styleText}</style>`;

function boxFromCorners(first, opposite) {
  return {
    x: Math.min(first[0], opposite[0]),
    y: Math.min(first[1], opposite[1]),
    width: Math.abs(opposite[0] - first[0]),
    height: Math.abs(opposite[1] - first[1]),
  };
}

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
    this._documentId = null;
    this._pdfDoc = null;
    this._loadingTask = null;
    this._chunks = [];
    this._questions = [];
    this._annotations = [];
    this._focusedAnnotationId = null;
    this._pendingSourceAnchor = null;
    this._pageSelectionContext = null;
    this._previousSelectionRange = null;
    this._hoveredHighlight = null;
    this._selectedQuestionId = null;
    this._showEvidenceOnly = false;
    this._currentPage = 1;
    this._renderId = 0;
    this._lastRenderedWidth = 0;
    this._resizeObserver = null;
    this._selectionChangeHandler = () => this.captureCurrentSelection();
    this._mouseUpHandler = () => this.resetEndOfContent();
  }

  connectedCallback() {
    this.render();
    this.observeViewerSize();
    document.addEventListener("selectionchange", this._selectionChangeHandler);
    window.addEventListener("mouseup", this._mouseUpHandler);
  }

  disconnectedCallback() {
    document.removeEventListener("selectionchange", this._selectionChangeHandler);
    window.removeEventListener("mouseup", this._mouseUpHandler);
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

  setDocumentId(documentId) {
    this._documentId = documentId;
  }

  setAnnotations(annotations) {
    if (JSON.stringify(annotations) === JSON.stringify(this._annotations)) return;
    this._annotations = annotations;
    this.renderAnnotationList();
    if (this._pdfDoc) void this.renderCurrentPage();
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
    this._pageSelectionContext = null;
    this.resetPendingSourceAnchor();
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
              <span id="evidence-filter-label">Show analyzed evidence only</span>
            </label>
          </div>
          <section class="annotations-section">
            <h3>Saved evidence</h3>
            <div class="annotations-list"></div>
          </section>
          <div class="chunks-list"></div>
        </aside>
        <main class="viewer">
          <div class="source-guide">
            <strong>Add manual evidence</strong>
            <span>Select text in the PDF, then choose Add evidence. Repeat to save more sources.</span>
          </div>
          <div class="viewer-controls">
            <button id="prev-page" type="button">Previous</button>
            <span class="page-info">
              Page <span id="current-page">1</span> of <span id="total-pages">-</span>
            </span>
            <button id="next-page" type="button">Next</button>
            <span id="selection-status" class="selection-status"></span>
            <button id="save-selection" class="save-selection" type="button" disabled>
              Add evidence
            </button>
            <button id="clear-selection" type="button" disabled>Clear</button>
          </div>
          <div id="viewer-content" class="viewer-content"></div>
        </main>
      </div>
    `;

    this.bindEvents();
    this.renderQuestionOptions();
    this.renderAnnotationList();
    this.updateFilters();
    this.updatePageControls();
    this.updateSelectionControls();
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
    const viewerContent = this.shadowRoot.getElementById("viewer-content");
    viewerContent.addEventListener("mousedown", (event) => {
      if (event.button !== 0) return;
      const textItem = event.target.closest(TEXT_ITEM);
      if (textItem) {
        this.resetPendingSourceAnchor();
        textItem.closest(".text-layer").classList.add("selecting");
      } else {
        // A selection starts on text. A press on blank space only clears the current one.
        event.preventDefault();
        this.clearPendingSourceAnchor();
      }
    });
    viewerContent.addEventListener("mousemove", (event) => this.updateHighlightHover(event));
    viewerContent.addEventListener("mouseleave", () => this.setHoveredHighlight());
    this.shadowRoot.getElementById("save-selection").addEventListener("click", () => {
      this.savePendingSourceAnchor();
    });
    this.shadowRoot.getElementById("clear-selection").addEventListener("click", () => {
      this.clearPendingSourceAnchor();
    });
    this.shadowRoot.querySelector(".annotations-list").addEventListener("click", (event) => {
      const item = event.target.closest(".source-annotation-item");
      if (!item) return;
      const annotation = this._annotations[Number(item.dataset.annotationIndex)];
      if (event.target.closest(".source-annotation-delete")) {
        this.dispatchSourceAnnotationChange("delete", annotation);
      } else {
        void this.openAnnotation(annotation);
      }
    });
  }

  async openAnnotation(annotation) {
    this._focusedAnnotationId = annotation.id;
    this.renderAnnotationList();
    await this.navigateToPage(annotation.page);
    this.shadowRoot.querySelector(".source-highlight.is-focused")?.scrollIntoView({ block: "nearest" });
  }

  // Highlights sit under the text layer, so they never receive mouse events themselves.
  updateHighlightHover({ buttons, clientX, clientY }) {
    if (buttons) return;
    const highlights = this.shadowRoot.querySelectorAll(".highlight");
    this.setHoveredHighlight([...highlights].find((highlight) => {
      const box = highlight.getBoundingClientRect();
      return clientX >= box.left && clientX <= box.right && clientY >= box.top && clientY <= box.bottom;
    }));
  }

  setHoveredHighlight(highlight = null) {
    if (highlight === this._hoveredHighlight) return;
    this._hoveredHighlight?.classList.remove("is-hovered");
    this._hoveredHighlight = highlight;
    highlight?.classList.add("is-hovered");
    const layer = this.shadowRoot.querySelector(".text-layer");
    if (layer) layer.title = highlight?.title ?? "";
  }

  renderAnnotationList() {
    const list = this.shadowRoot.querySelector(".annotations-list");
    if (!this._annotations.length) {
      list.innerHTML = '<div class="empty">No manual evidence saved yet</div>';
      return;
    }

    list.innerHTML = this._annotations.map((annotation, index) => `
      <div
        class="source-annotation-item ${annotation.id === this._focusedAnnotationId ? "is-active" : ""}"
        data-annotation-index="${index}"
      >
        <button class="source-annotation-open" type="button">
          <span class="source-annotation-title">Source ${index + 1} · Page ${annotation.page}</span>
          <span class="source-annotation-text">${this.escapeHtml(annotation.selected_text)}</span>
        </button>
        <button class="source-annotation-delete" type="button" aria-label="Remove source ${index + 1}">
          Remove
        </button>
      </div>
    `).join("");
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
        ? "Show analyzed evidence only"
        : "No analyzed evidence";
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
    this.clearPendingSourceAnchor();
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
      const textContent = await this.readTextContent(page);
      const { layer, pageText } = await this.renderTextLayer(textContent, viewport);
      if (renderId !== this._renderId) return;

      this._currentPage = pageNumber;
      this.updatePageControls();

      const pageContainer = document.createElement("div");
      pageContainer.className = "page-container";
      pageContainer.style.setProperty("--total-scale-factor", viewport.scale);
      pageContainer.append(canvas);

      const highlights = this.renderHighlights(textContent.items, viewport, pageNumber);
      if (highlights.childElementCount) pageContainer.append(highlights);
      const annotationLayer = this.renderSourceAnnotations(viewport, pageNumber);
      if (annotationLayer.childElementCount) pageContainer.append(annotationLayer);
      pageContainer.append(layer);

      this._pageSelectionContext = { pageText, pageContainer, viewport, pageNumber };
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

  // page.getTextContent() needs async-iterable streams, which Safari 18 lacks.
  async readTextContent(page) {
    const reader = page.streamTextContent().getReader();
    const textContent = { items: [], styles: {}, lang: null };
    try {
      while (true) {
        const { value, done } = await reader.read();
        if (done) return textContent;
        textContent.items.push(...value.items);
        Object.assign(textContent.styles, value.styles);
        textContent.lang ??= value.lang;
      }
    } finally {
      reader.releaseLock();
    }
  }

  async renderTextLayer(textContent, viewport) {
    const layer = document.createElement("div");
    layer.className = "text-layer";
    const textLayer = new pdfjsLib.TextLayer({
      textContentSource: textContent,
      container: layer,
      viewport,
    });
    await textLayer.render();
    const endOfContent = document.createElement("div");
    endOfContent.className = "end-of-content";
    layer.append(endOfContent);

    const textItems = textContent.items.filter((item) => typeof item.str === "string");
    return { layer, pageText: this.buildTextIndex(textItems, textLayer.textDivs) };
  }

  buildTextIndex(textItems, textDivs) {
    let pageText = "";
    textItems.forEach((item, index) => {
      textDivs[index].dataset.sourceTextStart = pageText.length;
      pageText += item.str;
      if (item.hasEOL) pageText += "\n";
    });
    return pageText;
  }

  captureCurrentSelection() {
    const context = this._pageSelectionContext;
    const range = context && this.getSelectionRange();
    if (!range || range.collapsed || !range.intersectsNode(context.pageContainer)) return;
    this.moveEndOfContent(range);
    this._pendingSourceAnchor = this.createSourceAnchor(range, context);
    this.updateSelectionControls();
  }

  createSourceAnchor(range, { pageText, pageContainer, viewport, pageNumber }) {
    const segments = this.getSelectionSegments(range, pageContainer);
    if (!segments.length || !this._documentId) return null;
    const first = segments[0];
    const last = segments.at(-1);
    const spanStart = Number(first.element.dataset.sourceTextStart) + first.start;
    const spanEnd = Number(last.element.dataset.sourceTextStart) + last.end;
    const selectedText = pageText.slice(spanStart, spanEnd);
    const rects = this.selectionRectsToPdf(segments, pageContainer, viewport);
    if (!selectedText.trim() || !rects.length) return null;

    return {
      id: this.createAnnotationId(),
      document_id: this._documentId,
      page: pageNumber,
      span_start: spanStart,
      span_end: spanEnd,
      selected_text: selectedText,
      rects,
    };
  }

  getSelectionRange() {
    const selection = window.getSelection();
    let composedRange;
    try {
      [composedRange] = selection.getComposedRanges({ shadowRoots: [this.shadowRoot] });
    } catch {
      // Safari 18 only accepts the shadow root itself.
      [composedRange] = selection.getComposedRanges(this.shadowRoot);
    }
    if (!composedRange) return null;
    const range = document.createRange();
    range.setStart(composedRange.startContainer, composedRange.startOffset);
    range.setEnd(composedRange.endContainer, composedRange.endOffset);
    return range;
  }

  needsEndOfContentMove() {
    const chromium = /\bChrome\/(\d+)\b/.exec(navigator.userAgent)?.[1];
    return !CSS.supports("-moz-user-select", "none") && !(Number(chromium) >= NATIVE_SELECTION_CHROMIUM);
  }

  // As in the PDF.js viewer: other browsers need the blank-space element next to the moving
  // end of the selection, or the selection jumps across the page.
  moveEndOfContent(range) {
    if (!this.needsEndOfContentMove()) return;
    const previous = this._previousSelectionRange;
    const modifyStart = previous && (
      range.compareBoundaryPoints(Range.END_TO_END, previous) === 0 ||
      range.compareBoundaryPoints(Range.START_TO_END, previous) === 0
    );
    this._previousSelectionRange = range.cloneRange();

    let anchor = modifyStart ? range.startContainer : range.endContainer;
    if (anchor.nodeType === Node.TEXT_NODE) anchor = anchor.parentNode;
    const end = this.shadowRoot.querySelector(".end-of-content");
    if (anchor === end) return;
    if (!modifyStart && range.endOffset === 0 && !anchor.matches(".text-layer")) {
      do {
        while (anchor && !anchor.previousSibling) anchor = anchor.parentNode;
        anchor = anchor?.previousSibling;
      } while (anchor && !anchor.childNodes.length);
    }
    if (anchor?.parentElement?.closest(".text-layer")) {
      end.style.userSelect = "text";
      anchor.parentElement.insertBefore(end, modifyStart ? anchor : anchor.nextSibling);
    }
  }

  resetEndOfContent() {
    this._previousSelectionRange = null;
    const layer = this.shadowRoot.querySelector(".text-layer");
    if (!layer) return;
    const end = layer.querySelector(".end-of-content");
    layer.append(end);
    end.style.userSelect = "";
    layer.classList.remove("selecting");
  }

  getSelectionSegments(range, pageContainer) {
    const segments = [];
    for (const element of pageContainer.querySelectorAll(TEXT_ITEM)) {
      if (!range.intersectsNode(element)) continue;
      const start = element.contains(range.startContainer)
        ? this.getTextOffset(element, range.startContainer, range.startOffset)
        : 0;
      const end = element.contains(range.endContainer)
        ? this.getTextOffset(element, range.endContainer, range.endOffset)
        : element.textContent.length;
      if (end > start) segments.push({ element, start, end });
    }
    return segments;
  }

  getTextOffset(textElement, container, offset) {
    const range = document.createRange();
    range.selectNodeContents(textElement);
    range.setEnd(container, offset);
    return range.toString().length;
  }

  selectionRectsToPdf(segments, pageContainer, viewport) {
    const pageRect = pageContainer.getBoundingClientRect();
    const rects = [];
    for (const { element, start, end } of segments) {
      const range = document.createRange();
      range.setStart(element.firstChild, start);
      range.setEnd(element.firstChild, end);
      for (const rect of range.getClientRects()) {
        const left = Math.max(0, rect.left - pageRect.left);
        const top = Math.max(0, rect.top - pageRect.top);
        const right = Math.min(viewport.width, rect.right - pageRect.left);
        const bottom = Math.min(viewport.height, rect.bottom - pageRect.top);
        if (right > left && bottom > top) {
          rects.push(boxFromCorners(
            viewport.convertToPdfPoint(left, top),
            viewport.convertToPdfPoint(right, bottom),
          ));
        }
      }
    }
    return rects;
  }

  renderSourceAnnotations(viewport, pageNumber) {
    const layer = document.createElement("div");
    layer.className = "source-annotations-layer";
    for (const annotation of this._annotations) {
      if (annotation.page !== pageNumber) continue;
      const className = `source-highlight ${annotation.id === this._focusedAnnotationId ? "is-focused" : ""}`;
      for (const { x, y, width, height } of annotation.rects) {
        const box = boxFromCorners(
          viewport.convertToViewportPoint(x, y),
          viewport.convertToViewportPoint(x + width, y + height),
        );
        layer.append(this.createPageBox(className, box, viewport));
      }
    }
    return layer;
  }

  createPageBox(className, box, viewport) {
    const element = document.createElement("div");
    element.className = className;
    element.style.left = `${(box.x / viewport.width) * 100}%`;
    element.style.top = `${(box.y / viewport.height) * 100}%`;
    element.style.width = `${(box.width / viewport.width) * 100}%`;
    element.style.height = `${(box.height / viewport.height) * 100}%`;
    return element;
  }

  savePendingSourceAnchor() {
    const anchor = this._pendingSourceAnchor;
    this.clearPendingSourceAnchor();
    this.dispatchSourceAnnotationChange("create", anchor);
  }

  dispatchSourceAnnotationChange(action, annotation) {
    this.dispatchEvent(new CustomEvent("source-annotation-change", { detail: { action, annotation } }));
  }

  clearPendingSourceAnchor() {
    this.resetPendingSourceAnchor();
    window.getSelection().removeAllRanges();
  }

  resetPendingSourceAnchor() {
    this._pendingSourceAnchor = null;
    this.updateSelectionControls();
  }

  updateSelectionControls() {
    const anchor = this._pendingSourceAnchor;
    this.shadowRoot.getElementById("save-selection").disabled = !anchor;
    this.shadowRoot.getElementById("clear-selection").disabled = !anchor;
    this.shadowRoot.getElementById("selection-status").textContent = anchor?.selected_text ?? "";
  }

  // randomUUID only exists over HTTPS or on localhost.
  createAnnotationId() {
    return crypto.randomUUID?.() ?? `source-${Date.now()}-${Math.random().toString(16).slice(2)}`;
  }

  renderHighlights(textItems, viewport, pageNumber) {
    const layer = document.createElement("div");
    layer.className = "page-highlights";

    const chunks = this.getFilteredChunks().filter(
      (chunk) => chunk.question_id && this.getChunkPage(chunk) === pageNumber,
    );

    for (const chunk of chunks) {
      const boxes = this.findChunkTextPositions(textItems, chunk.text, viewport);
      for (const box of boxes) {
        const className = `highlight ${this.isEvidenceChunk(chunk) ? "evidence" : ""}`;
        const highlight = this.createPageBox(className, box, viewport);
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
    const box = boxFromCorners(
      viewport.convertToViewportPoint(minX, minY),
      viewport.convertToViewportPoint(maxX, maxY),
    );
    return box.width < 1 || box.height < 1 ? null : box;
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
