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
const originalToHexDescriptor = Object.getOwnPropertyDescriptor(
  Uint8Array.prototype,
  "toHex",
);
const originalToBase64Descriptor = Object.getOwnPropertyDescriptor(
  Uint8Array.prototype,
  "toBase64",
);
const originalFromBase64Descriptor = Object.getOwnPropertyDescriptor(
  Uint8Array,
  "fromBase64",
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
  restoreProperty(Uint8Array.prototype, "toHex", originalToHexDescriptor);
  restoreProperty(Uint8Array.prototype, "toBase64", originalToBase64Descriptor);
  restoreProperty(Uint8Array, "fromBase64", originalFromBase64Descriptor);
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

  it("polyfills the byte encodings pdf.js uses to open a document", async () => {
    delete Uint8Array.prototype.toHex;
    delete Uint8Array.prototype.toBase64;
    delete Uint8Array.fromBase64;

    await import(`./pdfjs-map-polyfill.js?bytes=${Date.now()}`);

    const hello = new Uint8Array([72, 101, 108, 108, 111]);
    expect(hello.toHex()).toBe("48656c6c6f");
    expect(hello.toBase64()).toBe("SGVsbG8=");
    expect(Array.from(Uint8Array.fromBase64("SGVsbG8="))).toEqual([
      72, 101, 108, 108, 111,
    ]);
    expect(new Uint8Array(16).toHex()).toHaveLength(32);
  });
});
