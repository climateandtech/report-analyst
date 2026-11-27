import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("pdfjs-dist/build/pdf.mjs", () => ({
  GlobalWorkerOptions: { workerSrc: "" },
  getDocument: vi.fn(),
}));

const { default: PdfViewerWithChunks } = await import("./pdf-viewer.js");

function createViewport() {
  return {
    width: 600,
    height: 800,
    convertToViewportPoint: (x, y) => [x, 800 - y],
  };
}

function textItem(str, x, y, width) {
  return { str, transform: [1, 0, 0, 10, x, y], width, height: 10 };
}

describe("PDF viewer", () => {
  let viewer;

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  beforeEach(() => {
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

  it("shows chunk-only PDFs as unmapped with evidence unavailable", () => {
    viewer._chunks = [
      { text: "Unmapped report chunk", metadata: { page_number: 1 } },
    ];

    viewer.render();

    const options = [...viewer.shadowRoot.getElementById("question-select").options];
    const evidenceFilter = viewer.shadowRoot.getElementById("evidence-filter");
    expect(options.map((option) => option.text)).toContain("Unmapped chunks");
    expect(evidenceFilter.disabled).toBe(true);
    expect(viewer.shadowRoot.getElementById("evidence-filter-label").textContent)
      .toBe("Evidence unavailable");
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
      getViewport: vi.fn(({ scale }) => ({ width: 600 * scale, height: 800 * scale })),
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

  it("keeps the purple fill transparent until a highlight is hovered", () => {
    viewer.render();

    const styles = viewer.shadowRoot.querySelector("style").textContent;
    expect(styles).toContain(".highlight:hover");
    expect(styles).toMatch(/\.highlight\s*\{[^}]*background:\s*transparent;/s);
    expect(styles).toMatch(/\.highlight\.evidence:hover\s*\{[^}]*rgba\(67, 19, 200, 0\.3\)/s);
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

  it("describes scores and order when an analyst hovers a highlight", () => {
    expect(
      viewer.getChunkTooltip({
        is_evidence: true,
        similarity_score: 0.85,
        llm_score: 0.7,
        chunk_order: 2,
      }),
    ).toBe("Evidence | Similarity: 0.850 | LLM: 0.700 | Chunk order: 3");
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
