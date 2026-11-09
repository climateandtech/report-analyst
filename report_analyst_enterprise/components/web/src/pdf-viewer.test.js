import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("pdfjs-dist/build/pdf.mjs", () => ({
  GlobalWorkerOptions: { workerSrc: "" },
  getDocument: vi.fn(),
  TextLayer: class TextLayer {
    constructor({ textContentSource, container }) {
      this.textContentSource = textContentSource;
      this.container = container;
      this.textDivs = [];
    }

    async render() {
      for (const item of this.textContentSource.items || []) {
        if (typeof item.str !== "string") continue;
        const span = document.createElement("span");
        span.textContent = item.str;
        this.textDivs.push(span);
        this.container.append(span);
      }
    }
  },
}));

const { default: PdfViewerWithChunks } = await import("./pdf-viewer.js");

function createViewport() {
  return {
    width: 600,
    height: 800,
    scale: 1,
    convertToPdfPoint: (x, y) => [x, 800 - y],
    convertToViewportPoint: (x, y) => [x, 800 - y],
  };
}

function textItem(str, x, y, width) {
  return { str, transform: [1, 0, 0, 10, x, y], width, height: 10 };
}

function clientBox(left, top, width, height) {
  return { left, top, width, height, right: left + width, bottom: top + height };
}

// jsdom has no layout. Browsers report one box per text line a range touches, plus the
// element's own box when the range fully contains that element.
function stubRangeRects(boxes) {
  Range.prototype.getClientRects = function getClientRects() {
    return [...boxes].flatMap(([element, box]) => {
      if (!this.intersectsNode(element)) return [];
      const fullyContained = this.comparePoint(element, 0) === 0 &&
        this.comparePoint(element, element.childNodes.length) === 0;
      return fullyContained ? [box, box] : [box];
    });
  };
}

// Three text lines at y = 30, 45 and 60, on a page container positioned at (10, 20).
async function renderSelectablePage(viewer) {
  viewer.render();
  viewer.setDocumentId("document-hash");
  viewer.createAnnotationId = () => "annotation-id";
  const viewport = createViewport();
  const { layer, pageText } = await viewer.renderTextLayer(
    {
      items: ["Scope 1 emissions", "123,400 tCO2e", "Verified by auditor"]
        .map((str) => ({ str, hasEOL: true })),
    },
    viewport,
  );
  const pageContainer = document.createElement("div");
  pageContainer.getBoundingClientRect = () => ({ left: 10, top: 20 });
  pageContainer.append(layer);
  viewer.shadowRoot.getElementById("viewer-content").replaceChildren(pageContainer);
  viewer._pageSelectionContext = { pageText, pageContainer, viewport, pageNumber: 4 };
  const spans = [...layer.querySelectorAll("[data-source-text-start]")];
  stubRangeRects(new Map(spans.map((span, index) => [span, clientBox(20, 30 + index * 15, 100, 10)])));
  return { layer, spans, lines: spans.map((span) => span.firstChild) };
}

function createRange(startNode, startOffset, endNode, endOffset) {
  const range = document.createRange();
  range.setStart(startNode, startOffset);
  range.setEnd(endNode, endOffset);
  return range;
}

function stubSelection(viewer, range) {
  const selection = {
    removeAllRanges: vi.fn(),
    getComposedRanges: ({ shadowRoots }) => (shadowRoots.includes(viewer.shadowRoot) && range ? [range] : []),
  };
  vi.spyOn(window, "getSelection").mockReturnValue(selection);
  return selection;
}

function select(viewer, range) {
  stubSelection(viewer, range);
  viewer.captureCurrentSelection();
  return viewer._pendingSourceAnchor;
}

function pdfLine(y) {
  return { x: 10, y, width: 100, height: 10 };
}

function press(target, init) {
  const event = new MouseEvent("mousedown", { bubbles: true, cancelable: true, ...init });
  target.dispatchEvent(event);
  return event;
}

// jsdom only applies document stylesheets, so the viewer's styles are copied there.
function appliedStyle(viewer, element, property, target = element) {
  viewer.render();
  const style = document.createElement("style");
  style.textContent = viewer.shadowRoot.querySelector("style").textContent;
  document.head.append(style);
  document.body.append(element);
  const value = getComputedStyle(target).getPropertyValue(property);
  style.remove();
  element.remove();
  return value;
}

const SAFARI_18_4 = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.4 Safari/605.1.15";
const CHROME_147 = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36";
const CHROME_148 = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36";
const FIREFOX = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:140.0) Gecko/20100101 Firefox/140.0";

describe("PDF viewer", () => {
  let viewer;

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
    delete Range.prototype.getClientRects;
    delete Element.prototype.scrollIntoView;
  });

  beforeEach(() => {
    vi.stubGlobal("CSS", { supports: () => false });
    viewer = new PdfViewerWithChunks();
    viewer._chunks = [
      {
        text: "Q1 evidence",
        question_id: "q1",
        is_evidence: true,
        chunk_order: 0,
        metadata: { page_number: 2 },
      },
      {
        text: "Q1 retrieved",
        question_id: "q1",
        is_evidence: false,
        chunk_order: 1,
        metadata: { page_number: 3 },
      },
      {
        text: "Q2 evidence",
        question_id: "q2",
        is_evidence: 1,
        chunk_order: 0,
        metadata: { page_number: 4 },
      },
    ];
    viewer._questions = [
      { question_id: "q1", text: "Question one" },
      { question_id: "q2", text: "Question two" },
    ];
  });

  it("shows chunks for every question by default", () => {
    expect(viewer.getFilteredChunks()).toHaveLength(3);
  });

  it("shows only chunks for the selected question", () => {
    viewer._selectedQuestionId = "q1";

    expect(viewer.getFilteredChunks().map((chunk) => chunk.text)).toEqual([
      "Q1 evidence",
      "Q1 retrieved",
    ]);
  });

  it("returns to all questions when the question filter is cleared", () => {
    viewer.setSelectedQuestionId("q1");
    expect(viewer.getFilteredChunks()).toHaveLength(2);

    viewer.setSelectedQuestionId(null);
    expect(viewer.getFilteredChunks()).toHaveLength(3);
  });

  it("treats booleans and SQLite integers as evidence", () => {
    viewer._showEvidenceOnly = true;

    expect(viewer.getFilteredChunks().map((chunk) => chunk.text)).toEqual([
      "Q1 evidence",
      "Q2 evidence",
    ]);
  });

  it("restores retrieved chunks when evidence-only is disabled", () => {
    viewer._showEvidenceOnly = true;
    expect(viewer.getFilteredChunks()).toHaveLength(2);

    viewer._showEvidenceOnly = false;
    expect(viewer.getFilteredChunks()).toHaveLength(3);
  });

  it("combines question and evidence filters", () => {
    viewer._selectedQuestionId = "q1";
    viewer._showEvidenceOnly = true;

    expect(viewer.getFilteredChunks().map((chunk) => chunk.text)).toEqual(["Q1 evidence"]);
  });

  it("redraws PDF highlights when either filter changes", () => {
    viewer._pdfDoc = { numPages: 10 };
    viewer.shadowRoot.innerHTML = `
      <select id="question-select"></select>
      <input id="evidence-filter" type="checkbox">
      <div class="chunks-list"></div>
    `;
    viewer.renderChunkList = vi.fn();
    viewer.renderCurrentPage = vi.fn().mockResolvedValue(undefined);

    viewer.setSelectedQuestionId("q1");
    viewer.setShowEvidenceOnly(true);

    expect(viewer.renderChunkList).toHaveBeenCalledTimes(2);
    expect(viewer.renderCurrentPage).toHaveBeenCalledTimes(2);
  });

  it("clears a question filter that is absent from new results", () => {
    viewer._selectedQuestionId = "q1";
    viewer.updateFilters = vi.fn();

    viewer.setQuestions([{ question_id: "q2", text: "Question two" }]);

    expect(viewer._selectedQuestionId).toBeNull();
    expect(viewer.updateFilters).toHaveBeenCalledOnce();
  });

  it("shows chunk-only PDFs as unmapped without analyzed evidence", () => {
    viewer._chunks = [
      { text: "Unmapped report chunk", metadata: { page_number: 1 } },
    ];

    viewer.render();

    const options = [...viewer.shadowRoot.getElementById("question-select").options];
    const evidenceFilter = viewer.shadowRoot.getElementById("evidence-filter");
    expect(options.map((option) => option.text)).toContain("Unmapped chunks");
    expect(evidenceFilter.disabled).toBe(true);
    expect(viewer.shadowRoot.getElementById("evidence-filter-label").textContent)
      .toBe("No analyzed evidence");
    expect(viewer.shadowRoot.querySelector(".chunk-item").textContent).toContain("Unmapped");

    viewer.setSelectedQuestionId("__unmapped__");
    viewer.setQuestions(viewer._questions);
    expect(viewer._selectedQuestionId).toBe("__unmapped__");
  });

  it("shows mapped questions without enabling the evidence filter", () => {
    viewer._chunks = [
      { text: "Mapped report chunk", question_id: "q1", metadata: { page_number: 1 } },
      { text: "Other mapped chunk", question_id: "q2", metadata: { page_number: 2 } },
    ];

    viewer.render();
    viewer.setSelectedQuestionId("q1");

    const questionOption = [...viewer.shadowRoot.getElementById("question-select").options]
      .find((option) => option.value === "q1");
    expect(questionOption.text).toContain("Mapped");
    expect(viewer.shadowRoot.getElementById("evidence-filter").disabled).toBe(true);
    expect(viewer.getFilteredChunks().map((chunk) => chunk.text)).toEqual([
      "Mapped report chunk",
    ]);
    expect(viewer.shadowRoot.querySelector(".chunk-item").textContent).toContain("Mapped");
  });

  it("keeps manual evidence separate from the analyzed-evidence filter", () => {
    viewer._chunks = [
      { text: "Mapped report chunk", question_id: "q1", metadata: { page_number: 1 } },
    ];
    viewer.render();

    viewer.setAnnotations([{ id: "annotation-id", page: 1, selected_text: "Manual evidence" }]);

    const evidenceFilter = viewer.shadowRoot.getElementById("evidence-filter");
    expect(evidenceFilter.disabled).toBe(true);
    expect(evidenceFilter.checked).toBe(false);
    expect(viewer.shadowRoot.getElementById("evidence-filter-label").textContent)
      .toBe("No analyzed evidence");
    expect(viewer.shadowRoot.querySelector(".source-annotation-text").textContent)
      .toBe("Manual evidence");
  });

  it("keeps analyzed evidence visible when manual evidence is added", () => {
    viewer.render();
    viewer.setShowEvidenceOnly(true);
    const evidenceBefore = viewer.getFilteredChunks().map((chunk) => chunk.text);

    viewer.setAnnotations([{ id: "annotation-id", page: 2, selected_text: "Manual evidence" }]);

    expect(viewer.getFilteredChunks().map((chunk) => chunk.text)).toEqual(evidenceBefore);
    expect(viewer.shadowRoot.getElementById("evidence-filter").checked).toBe(true);
  });

  it("identifies analyzed, mapped, and unmapped questions", () => {
    viewer._chunks = [
      { text: "Analyzed chunk", question_id: "q1", is_evidence: false },
      { text: "Mapped chunk", question_id: "q2" },
    ];
    viewer._questions.push({ question_id: "q3", text: "Question three" });

    viewer.render();

    const options = Object.fromEntries(
      [...viewer.shadowRoot.getElementById("question-select").options]
        .map((option) => [option.value, option.text]),
    );
    expect(options.q1).toContain("Analyzed");
    expect(options.q2).toContain("Mapped");
    expect(options.q3).toContain("Not mapped");

    viewer.setSelectedQuestionId("q1");
    expect(viewer.shadowRoot.getElementById("evidence-filter").disabled).toBe(false);
    viewer.setShowEvidenceOnly(true);
    viewer.setSelectedQuestionId("q2");
    expect(viewer.shadowRoot.getElementById("evidence-filter").disabled).toBe(true);
    expect(viewer._showEvidenceOnly).toBe(false);
  });

  it("returns an empty collection when no chunks match", () => {
    viewer._selectedQuestionId = "missing-question";

    expect(viewer.getFilteredChunks()).toEqual([]);
  });

  it("jumps from a chunk to its PDF page", async () => {
    viewer.navigateToPage = vi.fn().mockResolvedValue(undefined);

    await viewer.navigateToChunk(viewer._chunks[1]);

    expect(viewer.navigateToPage).toHaveBeenCalledWith(3);
  });

  it("does not highlight unmapped chunks by default", () => {
    viewer._chunks = [
      { text: "First unmapped report chunk with enough matching words", metadata: { page_number: 1 } },
      { text: "Second unmapped report chunk with enough matching words", metadata: { page_number: 1 } },
    ];
    viewer.findChunkTextPositions = vi.fn().mockReturnValue([
      { x: 10, y: 20, width: 100, height: 30 },
    ]);

    const highlights = viewer.renderHighlights([], createViewport(), 1);

    expect(highlights.childElementCount).toBe(0);
    expect(viewer.findChunkTextPositions).not.toHaveBeenCalled();
  });

  it("navigates to an unmapped chunk without highlighting it", async () => {
    const selectedChunk = {
      text: "Selected unmapped report chunk with enough matching words",
      metadata: { page_number: 1 },
    };
    viewer._chunks = [
      selectedChunk,
      { text: "Other unmapped report chunk with enough matching words", metadata: { page_number: 1 } },
    ];
    viewer.navigateToPage = vi.fn().mockResolvedValue(undefined);
    viewer.findChunkTextPositions = vi.fn().mockReturnValue([
      { x: 10, y: 20, width: 100, height: 30 },
    ]);

    await viewer.navigateToChunk(selectedChunk);
    const highlights = viewer.renderHighlights([], createViewport(), 1);

    expect(viewer.navigateToPage).toHaveBeenCalledWith(1);
    expect(highlights.childElementCount).toBe(0);
    expect(viewer.findChunkTextPositions).not.toHaveBeenCalled();
  });

  it("keeps question and evidence filters while changing pages", async () => {
    viewer.render();
    viewer._selectedQuestionId = "q1";
    viewer._showEvidenceOnly = true;
    viewer.loadPdf = vi.fn().mockResolvedValue({ numPages: 10 });
    viewer.renderCurrentPage = vi.fn().mockResolvedValue(undefined);

    await viewer.navigateToPage(2);

    expect(viewer._currentPage).toBe(2);
    expect(viewer._selectedQuestionId).toBe("q1");
    expect(viewer._showEvidenceOnly).toBe(true);
  });

  it("updates the page indicator when navigating", async () => {
    viewer.render();
    viewer._pdfDoc = { numPages: 10 };
    viewer.renderCurrentPage = vi.fn().mockResolvedValue(undefined);

    await viewer.navigateToPage(3);

    expect(viewer.shadowRoot.getElementById("current-page").textContent).toBe("3");
    expect(viewer.shadowRoot.getElementById("total-pages").textContent).toBe("10");
  });

  it("wires the next and previous controls to adjacent pages", () => {
    viewer.render();
    viewer._currentPage = 2;
    viewer._pdfDoc = { numPages: 4 };
    viewer.navigateToPage = vi.fn().mockResolvedValue(undefined);
    viewer.updatePageControls();

    viewer.shadowRoot.getElementById("next-page").click();
    viewer.shadowRoot.getElementById("prev-page").click();

    expect(viewer.navigateToPage).toHaveBeenCalledWith(3);
    expect(viewer.navigateToPage).toHaveBeenCalledWith(1);
  });

  it("renders the matching filtered chunk as a PDF highlight", async () => {
    viewer._currentPage = 2;
    viewer._selectedQuestionId = "q1";
    viewer._showEvidenceOnly = true;
    viewer.render();
    Object.defineProperty(viewer.shadowRoot.getElementById("viewer-content"), "clientWidth", {
      value: 640,
    });

    const page = {
      getViewport: vi.fn(({ scale }) => ({
        ...createViewport(),
        scale,
        width: 600 * scale,
        height: 800 * scale,
      })),
      streamTextContent: vi.fn().mockReturnValue(new ReadableStream({
        start(controller) {
          controller.enqueue({ items: [] });
          controller.close();
        },
      })),
    };
    const pdfDoc = { numPages: 4, getPage: vi.fn().mockResolvedValue(page) };
    const sourceCanvas = document.createElement("canvas");
    viewer.loadPdf = vi.fn().mockResolvedValue(pdfDoc);
    viewer.renderPage = vi.fn().mockResolvedValue(sourceCanvas);
    viewer.findChunkTextPositions = vi.fn().mockReturnValue([
      { x: 10, y: 20, width: 100, height: 30 },
    ]);

    await viewer.renderCurrentPage();

    const highlights = viewer.shadowRoot.querySelectorAll(".highlight");
    expect(highlights).toHaveLength(1);
    expect(highlights[0].title).toContain("Evidence");
    expect(viewer.findChunkTextPositions).toHaveBeenCalledWith(
      [],
      "Q1 evidence",
      expect.any(Object),
    );
  });

  it("maps rendered text items to stable page-text offsets", () => {
    const first = document.createElement("span");
    const second = document.createElement("span");

    const pageText = viewer.buildTextIndex(
      [
        { str: "Scope 1 emissions", hasEOL: true },
        { str: "123,400 tCO2e", hasEOL: false },
      ],
      [first, second],
    );

    expect(pageText).toBe("Scope 1 emissions\n123,400 tCO2e");
    expect(first.dataset.sourceTextStart).toBe("0");
    expect(second.dataset.sourceTextStart).toBe("18");
  });

  it("creates a multiline SourceAnchor from the current text selection", async () => {
    const { lines } = await renderSelectablePage(viewer);

    const anchor = select(viewer, createRange(lines[0], 6, lines[1], 7));

    expect(anchor).toEqual({
      id: "annotation-id",
      document_id: "document-hash",
      page: 4,
      span_start: 6,
      span_end: 25,
      selected_text: "1 emissions\n123,400",
      rects: [780, 765].map(pdfLine),
    });
    expect(viewer.shadowRoot.getElementById("save-selection").disabled).toBe(false);
    expect(viewer.shadowRoot.getElementById("clear-selection").disabled).toBe(false);
    expect(viewer.shadowRoot.getElementById("selection-status").textContent).toBe("1 emissions\n123,400");
  });

  it.each([
    {
      gesture: "a drag released past the end of a line",
      range: ({ layer, lines }) => createRange(lines[0], 6, layer, 2),
      span: [6, 31],
      text: "1 emissions\n123,400 tCO2e",
      lineTops: [780, 765],
    },
    {
      gesture: "a triple click that ends at the start of the next line",
      range: ({ spans, lines }) => createRange(lines[0], 0, spans[1], 0),
      span: [0, 17],
      text: "Scope 1 emissions",
      lineTops: [780],
    },
    {
      gesture: "a backwards drag that starts on blank space",
      range: ({ layer, lines }) => createRange(layer, 1, lines[1], 7),
      span: [18, 25],
      text: "123,400",
      lineTops: [765],
    },
  ])("captures $gesture", async ({ range, span, text, lineTops }) => {
    // Chrome leaves the blank-space element in place. Moving it here would hit a jsdom bug:
    // a node inserted into a range's start container also shifts the range's end.
    vi.spyOn(navigator, "userAgent", "get").mockReturnValue(CHROME_148);
    const page = await renderSelectablePage(viewer);

    const anchor = select(viewer, range(page));

    expect(anchor).toMatchObject({ span_start: span[0], span_end: span[1], selected_text: text });
    expect(anchor.rects).toEqual(lineTops.map(pdfLine));
  });

  it("stores one rectangle per line when a line is fully selected", async () => {
    const { lines } = await renderSelectablePage(viewer);

    const anchor = select(viewer, createRange(lines[0], 6, lines[2], 8));

    expect(anchor.selected_text).toBe("1 emissions\n123,400 tCO2e\nVerified");
    expect(anchor.rects).toEqual([780, 765, 750].map(pdfLine));
  });

  it("captures a selection in Safari, which only accepts the shadow root", async () => {
    const { lines } = await renderSelectablePage(viewer);
    vi.spyOn(window, "getSelection").mockReturnValue({
      getComposedRanges: (shadowRoot) => {
        if (shadowRoot !== viewer.shadowRoot) throw new TypeError("Argument 1 must be a ShadowRoot");
        return [createRange(lines[0], 6, lines[1], 7)];
      },
    });

    viewer.captureCurrentSelection();

    expect(viewer._pendingSourceAnchor.selected_text).toBe("1 emissions\n123,400");
  });

  it("keeps a pending selection when the selection is empty or collapsed", async () => {
    const { lines } = await renderSelectablePage(viewer);
    const anchor = { selected_text: "Pending evidence" };
    viewer._pendingSourceAnchor = anchor;

    expect(select(viewer, null)).toBe(anchor);
    expect(select(viewer, createRange(lines[0], 3, lines[0], 3))).toBe(anchor);
  });

  it("ignores text selected outside the PDF page", async () => {
    await renderSelectablePage(viewer);
    const anchor = { selected_text: "Pending evidence" };
    viewer._pendingSourceAnchor = anchor;
    const guide = viewer.shadowRoot.querySelector(".source-guide");

    expect(select(viewer, createRange(guide, 0, guide, 1))).toBe(anchor);
  });

  it.each([
    ["only whitespace is selected", ({ lines }) => createRange(lines[0], 5, lines[0], 6)],
    ["the selection has no text", ({ layer }) => createRange(layer, 3, layer, 4)],
  ])("creates no anchor when %s", async (_, range) => {
    const page = await renderSelectablePage(viewer);
    viewer._pendingSourceAnchor = { selected_text: "Pending evidence" };

    expect(select(viewer, range(page))).toBeNull();
  });

  it("creates no anchor for a PDF without a document id", async () => {
    const { lines } = await renderSelectablePage(viewer);
    viewer.setDocumentId(null);

    expect(select(viewer, createRange(lines[0], 0, lines[0], 5))).toBeNull();
  });

  it("creates no anchor for text outside the page area", async () => {
    const { spans, lines } = await renderSelectablePage(viewer);
    stubRangeRects(new Map([[spans[0], clientBox(700, 30, 50, 10)]]));

    expect(select(viewer, createRange(lines[0], 0, lines[0], 5))).toBeNull();
  });

  it("captures the selection when it changes", async () => {
    document.body.append(viewer);
    const { lines } = await renderSelectablePage(viewer);
    stubSelection(viewer, createRange(lines[0], 0, lines[0], 5));

    document.dispatchEvent(new Event("selectionchange"));

    expect(viewer._pendingSourceAnchor.selected_text).toBe("Scope");
    viewer.remove();
  });

  it("stops listening once removed from the page", () => {
    viewer.captureCurrentSelection = vi.fn();
    viewer.resetEndOfContent = vi.fn();
    document.body.append(viewer);
    viewer.remove();

    document.dispatchEvent(new Event("selectionchange"));
    window.dispatchEvent(new MouseEvent("mouseup"));

    expect(viewer.captureCurrentSelection).not.toHaveBeenCalled();
    expect(viewer.resetEndOfContent).not.toHaveBeenCalled();
  });

  it.each([
    ["Safari 18.4", SAFARI_18_4, false, true],
    ["Chrome 147", CHROME_147, false, true],
    ["Chrome 148", CHROME_148, false, false],
    ["Firefox", FIREFOX, true, false],
  ])("moves the blank-space element to the selection end only where needed: %s", async (_, userAgent, firefox, moves) => {
    vi.spyOn(navigator, "userAgent", "get").mockReturnValue(userAgent);
    vi.stubGlobal("CSS", { supports: () => firefox });
    const { layer, spans, lines } = await renderSelectablePage(viewer);
    const end = layer.querySelector(".end-of-content");

    select(viewer, createRange(lines[0], 0, lines[1], 5));

    expect(spans[1].nextSibling === end).toBe(moves);
    expect(layer.lastElementChild === end).toBe(!moves);
  });

  it("restores the blank-space element when the mouse is released outside the viewer", async () => {
    document.body.append(viewer);
    vi.spyOn(navigator, "userAgent", "get").mockReturnValue(SAFARI_18_4);
    const { layer, spans, lines } = await renderSelectablePage(viewer);
    const end = layer.querySelector(".end-of-content");
    press(spans[0]);
    select(viewer, createRange(lines[0], 0, lines[1], 5));
    expect(layer.classList.contains("selecting")).toBe(true);
    expect(end.style.userSelect).toBe("text");

    document.body.dispatchEvent(new MouseEvent("mouseup", { bubbles: true }));

    expect(layer.classList.contains("selecting")).toBe(false);
    expect(layer.lastElementChild).toBe(end);
    expect(end.style.userSelect).toBe("");
    viewer.remove();
  });

  it("starts a new selection when text is pressed", async () => {
    const { spans } = await renderSelectablePage(viewer);
    viewer._pendingSourceAnchor = { selected_text: "Pending evidence" };
    viewer.updateSelectionControls();

    expect(press(spans[0]).defaultPrevented).toBe(false);
    expect(viewer.shadowRoot.getElementById("save-selection").disabled).toBe(true);
  });

  it("only clears the selection when blank page space is pressed", async () => {
    const { layer } = await renderSelectablePage(viewer);
    const { removeAllRanges } = stubSelection(viewer);
    viewer._pendingSourceAnchor = { selected_text: "Pending evidence" };

    expect(press(layer).defaultPrevented).toBe(true);
    expect(viewer._pendingSourceAnchor).toBeNull();
    expect(removeAllRanges).toHaveBeenCalledOnce();
    expect(layer.classList.contains("selecting")).toBe(false);
  });

  it("keeps the pending selection on a right click or a press outside the page", async () => {
    const { spans } = await renderSelectablePage(viewer);
    const anchor = { selected_text: "Pending evidence" };
    viewer._pendingSourceAnchor = anchor;

    press(spans[0], { button: 2 });
    press(viewer.shadowRoot.getElementById("save-selection"));

    expect(viewer._pendingSourceAnchor).toBe(anchor);
  });

  it("clears a pending selection from the viewer controls", () => {
    viewer.render();
    const { removeAllRanges } = stubSelection(viewer);
    viewer._pendingSourceAnchor = { selected_text: "Pending evidence" };
    viewer.updateSelectionControls();

    viewer.shadowRoot.getElementById("clear-selection").click();

    expect(viewer._pendingSourceAnchor).toBeNull();
    expect(removeAllRanges).toHaveBeenCalledOnce();
    expect(viewer.shadowRoot.getElementById("clear-selection").disabled).toBe(true);
  });

  it("submits repeated and overlapping source selections to the Streamlit bridge", () => {
    viewer.render();
    const firstAnchor = {
      id: "value-source",
      document_id: "document-hash",
      page: 2,
      span_start: 20,
      span_end: 27,
      selected_text: "123,400",
      rects: [{ x: 20, y: 30, width: 40, height: 10 }],
    };
    const secondAnchor = { ...firstAnchor, id: "unit-source", selected_text: "tCO2e" };
    const { removeAllRanges } = stubSelection(viewer);
    viewer._annotations = [{ ...firstAnchor, id: "disclosure-source", span_start: 0 }];
    const listener = vi.fn();
    viewer.addEventListener("source-annotation-change", listener);

    viewer._pendingSourceAnchor = firstAnchor;
    viewer.savePendingSourceAnchor();
    viewer._pendingSourceAnchor = secondAnchor;
    viewer.savePendingSourceAnchor();

    expect(viewer._annotations).toHaveLength(1);
    expect(listener.mock.calls.map(([event]) => event.detail)).toEqual([
      { action: "create", annotation: firstAnchor },
      { action: "create", annotation: secondAnchor },
    ]);
    expect(removeAllRanges).toHaveBeenCalledTimes(2);
    expect(viewer.shadowRoot.getElementById("save-selection").disabled).toBe(true);
    expect(viewer.shadowRoot.getElementById("clear-selection").disabled).toBe(true);
  });

  it("renders saved PDF-coordinate rectangles and navigates from their list item", async () => {
    viewer.render();
    viewer.navigateToPage = vi.fn().mockResolvedValue(undefined);
    viewer.setAnnotations([
      {
        id: "annotation-id",
        page: 3,
        selected_text: "Selected disclosure",
        rects: [{ x: 25, y: 700, width: 125, height: 20 }],
      },
    ]);

    const layer = viewer.renderSourceAnnotations(createViewport(), 3);
    viewer.shadowRoot.querySelector(".source-annotation-item").click();

    expect(layer.querySelectorAll(".source-highlight")).toHaveLength(1);
    expect(layer.querySelector(".source-highlight").style.left).toBe("4.166666666666666%");
    expect(viewer.renderSourceAnnotations(createViewport(), 2).childElementCount).toBe(0);
    expect(viewer.navigateToPage).toHaveBeenCalledWith(3);
  });

  it("marks the saved source that was opened and scrolls it into view", async () => {
    viewer.render();
    const sentence = "The same disclosure sentence";
    viewer.setAnnotations([
      { id: "first", page: 3, selected_text: sentence, rects: [{ x: 25, y: 700, width: 125, height: 20 }] },
      { id: "second", page: 3, selected_text: sentence, rects: [{ x: 25, y: 100, width: 125, height: 20 }] },
    ]);
    const content = viewer.shadowRoot.getElementById("viewer-content");
    viewer.navigateToPage = vi.fn(async () => {
      content.replaceChildren(viewer.renderSourceAnnotations(createViewport(), 3));
    });
    const scrollIntoView = vi.fn();
    Element.prototype.scrollIntoView = scrollIntoView;

    viewer.shadowRoot.querySelectorAll(".source-annotation-open")[1].click();

    await vi.waitFor(() => expect(scrollIntoView).toHaveBeenCalledWith({ block: "nearest" }));
    expect(viewer.navigateToPage).toHaveBeenCalledWith(3);
    const highlights = [...content.querySelectorAll(".source-highlight")];
    expect(highlights.map((highlight) => highlight.classList.contains("is-focused"))).toEqual([false, true]);
    expect(scrollIntoView.mock.contexts[0]).toBe(highlights[1]);
    expect([...viewer.shadowRoot.querySelectorAll(".source-annotation-item")]
      .map((item) => item.classList.contains("is-active"))).toEqual([false, true]);
  });

  it("renders analyzed and manual evidence together", () => {
    viewer._currentPage = 2;
    viewer._showEvidenceOnly = true;
    viewer._annotations = [{
      id: "manual-source",
      page: 2,
      selected_text: "Manual evidence",
      rects: [{ x: 25, y: 700, width: 125, height: 20 }],
    }];
    viewer.findChunkTextPositions = vi.fn().mockReturnValue([
      { x: 10, y: 20, width: 100, height: 30 },
    ]);

    const chunkLayer = viewer.renderHighlights([], createViewport(), 2);
    const manualLayer = viewer.renderSourceAnnotations(createViewport(), 2);

    expect(chunkLayer.querySelectorAll(".highlight.evidence")).toHaveLength(1);
    expect(manualLayer.querySelectorAll(".source-highlight")).toHaveLength(1);
  });

  it("requests removal of saved evidence", () => {
    viewer.render();
    const annotation = {
      id: "annotation-id",
      page: 3,
      selected_text: "Selected disclosure",
      rects: [],
    };
    viewer.setAnnotations([annotation]);
    const listener = vi.fn();
    viewer.addEventListener("source-annotation-change", listener);

    viewer.shadowRoot.querySelector(".source-annotation-delete").click();

    expect(listener).toHaveBeenCalledOnce();
    expect(listener.mock.calls[0][0].detail).toEqual({
      action: "delete",
      annotation,
    });
  });

  it("uses separate highlight boxes for separate evidence lines", () => {
    const textItems = [
      textItem("First evidence line", 50, 700, 110),
      textItem("Second evidence line", 50, 680, 120),
    ];
    const searchText = "first evidence line second evidence line";

    const boxes = viewer.findChunkTextPositions(
      textItems,
      searchText,
      createViewport(),
    );

    expect(boxes).toHaveLength(2);
    expect(boxes.every((box) => box.height === 10)).toBe(true);
  });

  it("matches evidence despite a different prefix, punctuation, and hyphenation", () => {
    const textItems = [
      textItem("Annual report 2024", 50, 720, 100),
      textItem("Climate-related risks are reviewed annually.", 50, 700, 220),
    ];

    const boxes = viewer.findChunkTextPositions(
      textItems,
      "Retrieved context differs. Climate related risks are reviewed annually!",
      createViewport(),
    );

    expect(boxes).toHaveLength(1);
    expect(boxes[0].height).toBe(10);
  });

  it("does not highlight a short incidental match", () => {
    const textItems = [textItem("Climate risks are reviewed", 50, 700, 150)];

    const boxes = viewer.findChunkTextPositions(
      textItems,
      "Different evidence says climate risks are reviewed under another framework",
      createViewport(),
    );

    expect(boxes).toEqual([]);
  });

  it("keeps separated matches in separate highlight boxes", () => {
    const textItems = [
      textItem("alpha beta gamma delta epsilon zeta", 50, 700, 140),
      textItem("unrelated text between both matches", 200, 700, 130),
      textItem("eta theta iota kappa lambda mu", 350, 700, 140),
    ];
    const chunkText = [
      "alpha beta gamma delta epsilon zeta",
      "different words inside the extracted chunk",
      "eta theta iota kappa lambda mu",
    ].join(" ");

    const boxes = viewer.findChunkTextPositions(textItems, chunkText, createViewport());

    expect(boxes).toHaveLength(2);
  });

  it("keeps chunk highlights out of the text-selection path", () => {
    const layer = document.createElement("div");
    layer.className = "page-highlights";

    expect(appliedStyle(viewer, layer, "pointer-events")).toBe("none");
  });

  it.each([
    ["90", "rotate(90deg) translateY(-100%)"],
    ["180", "rotate(180deg) translate(-100%, -100%)"],
    ["270", "rotate(270deg) translateX(-100%)"],
  ])("turns the text layer with a page rotated %s degrees", (rotation, transform) => {
    const layer = document.createElement("div");
    layer.className = "text-layer";
    layer.setAttribute("data-main-rotation", rotation);

    expect(appliedStyle(viewer, layer, "transform")).toBe(transform);
  });

  it.each([
    ["--rotate", "0deg"],
    ["--scale-x", "1"],
  ])("defaults %s so text spans keep their PDF.js transform", (property, value) => {
    const layer = document.createElement("div");
    layer.className = "text-layer";
    const span = document.createElement("span");
    layer.append(span);

    expect(appliedStyle(viewer, layer, property, span)).toBe(value);
  });

  it("renders an explicit no-chunks state", () => {
    viewer.shadowRoot.innerHTML = '<div class="chunks-list"></div>';
    viewer._selectedQuestionId = "missing-question";

    viewer.renderChunkList();

    expect(viewer.shadowRoot.querySelector(".chunks-list").textContent).toContain(
      "No chunks to display",
    );
  });

  it("shows a clear error when the PDF cannot be loaded", async () => {
    viewer.shadowRoot.innerHTML = '<div id="viewer-content"></div>';
    viewer.loadPdf = vi.fn().mockRejectedValue(new Error("Unavailable"));

    await viewer.loadAndRenderPdf();

    expect(viewer.shadowRoot.getElementById("viewer-content").textContent).toContain(
      "Error loading PDF: Unavailable",
    );
  });

  describe("hovering a chunk highlight", () => {
    let highlight;
    let layer;
    const movePointer = (clientX, clientY, buttons = 0) => layer.dispatchEvent(
      new MouseEvent("mousemove", { clientX, clientY, buttons, bubbles: true }),
    );

    beforeEach(() => {
      viewer.render();
      viewer._chunks = [{
        text: "Scored evidence",
        question_id: "q1",
        is_evidence: true,
        similarity_score: 0.85,
        llm_score: 0.7,
        chunk_order: 2,
        metadata: { page_number: 2 },
      }];
      viewer.findChunkTextPositions = vi.fn().mockReturnValue([
        { x: 10, y: 20, width: 100, height: 30 },
      ]);
      const highlights = viewer.renderHighlights([], createViewport(), 2);
      highlight = highlights.querySelector(".highlight");
      highlight.getBoundingClientRect = () => clientBox(50, 50, 100, 30);
      layer = document.createElement("div");
      layer.className = "text-layer";
      viewer.shadowRoot.getElementById("viewer-content").append(highlights, layer);
    });

    it("shows the scores and order while the pointer is over it", () => {
      movePointer(100, 60);

      expect(layer.title).toBe("Evidence | Similarity: 0.850 | LLM: 0.700 | Chunk order: 3");
      expect(highlight.classList.contains("is-hovered")).toBe(true);
    });

    it("clears them when the pointer moves off the highlight", () => {
      movePointer(100, 60);
      movePointer(10, 10);

      expect(layer.title).toBe("");
      expect(highlight.classList.contains("is-hovered")).toBe(false);
    });

    it("clears them when the pointer leaves the page", () => {
      movePointer(100, 60);
      viewer.shadowRoot.getElementById("viewer-content").dispatchEvent(new MouseEvent("mouseleave"));

      expect(layer.title).toBe("");
      expect(highlight.classList.contains("is-hovered")).toBe(false);
    });

    it("stays out of the way during a drag selection", () => {
      movePointer(100, 60, 1);

      expect(layer.title).toBe("");
      expect(highlight.classList.contains("is-hovered")).toBe(false);
    });
  });

  it("fits the PDF page into the width remaining beside the chunks sidebar", () => {
    expect(viewer.getFitScale(600, 500)).toBeCloseTo(460 / 600);
    expect(viewer.getFitScale(600, 1200)).toBeCloseTo(1160 / 600);
  });

  it("rerenders the first page when its container width settles", () => {
    let resizeCallback;
    const observe = vi.fn();
    vi.stubGlobal("ResizeObserver", class ResizeObserver {
      constructor(callback) {
        resizeCallback = callback;
      }

      observe(target) {
        observe(target);
      }

      disconnect() {}
    });

    viewer.render();
    const content = viewer.shadowRoot.getElementById("viewer-content");
    let containerWidth = 80;
    Object.defineProperty(content, "clientWidth", {
      configurable: true,
      get: () => containerWidth,
    });
    viewer._pdfDoc = { numPages: 1 };
    viewer._lastRenderedWidth = containerWidth;
    viewer.renderCurrentPage = vi.fn().mockImplementation(() => {
      viewer._lastRenderedWidth = containerWidth;
    });

    viewer.observeViewerSize();
    expect(observe).toHaveBeenCalledWith(content);

    containerWidth = 640;
    resizeCallback();
    resizeCallback();

    expect(viewer.renderCurrentPage).toHaveBeenCalledOnce();
  });
});
