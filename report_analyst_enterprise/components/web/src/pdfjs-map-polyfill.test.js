import { afterEach, describe, expect, it } from "vitest";

const originalGetOrInsertDescriptor = Object.getOwnPropertyDescriptor(
  Map.prototype,
  "getOrInsert",
);
const originalGetOrInsertComputedDescriptor = Object.getOwnPropertyDescriptor(
  Map.prototype,
  "getOrInsertComputed",
);
const originalDomMatrixDescriptor = Object.getOwnPropertyDescriptor(
  globalThis,
  "DOMMatrix",
);
const originalPath2DDescriptor = Object.getOwnPropertyDescriptor(
  globalThis,
  "Path2D",
);

function restoreProperty(target, property, descriptor) {
  if (descriptor) {
    Object.defineProperty(target, property, descriptor);
  } else {
    delete target[property];
  }
}

afterEach(() => {
  restoreProperty(Map.prototype, "getOrInsert", originalGetOrInsertDescriptor);
  restoreProperty(
    Map.prototype,
    "getOrInsertComputed",
    originalGetOrInsertComputedDescriptor,
  );
  restoreProperty(globalThis, "DOMMatrix", originalDomMatrixDescriptor);
  restoreProperty(globalThis, "Path2D", originalPath2DDescriptor);
});

describe("PDF.js browser compatibility", () => {
  it("polyfills the Map insertion methods used by the production viewer", async () => {
    delete Map.prototype.getOrInsert;
    delete Map.prototype.getOrInsertComputed;
    globalThis.DOMMatrix = class DOMMatrix {};
    globalThis.Path2D = class Path2D {};

    await import(
      "../../streamlit_component/frontend/public/pdf-viewer.es.js"
    );

    const values = new Map([["existing", undefined]]);
    expect(values.getOrInsert("existing", "fallback")).toBeUndefined();
    expect(values.getOrInsert("new", "inserted")).toBe("inserted");
    expect(values.getOrInsertComputed("computed", (key) => `${key}-value`)).toBe(
      "computed-value",
    );
  });
});
