"use strict";

const assert = require("node:assert/strict");
const fs = require("fs");
const os = require("os");
const path = require("path");
const test = require("node:test");

const signer = require("./sign_python");

test("Mach-O headers are recognized and other files are not", () => {
  const macho = Buffer.alloc(4);
  macho.writeUInt32BE(0xfeedfacf, 0);
  assert.equal(signer.isMachO(macho), true);
  assert.equal(signer.isMachO(Buffer.from("text")), false);
  assert.equal(signer.isMachO(Buffer.alloc(2)), false);
});

test("only Mach-O files in the prefix are selected, deepest first", () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "osa-sign-"));
  const nested = path.join(root, "lib", "python3.12", "site-packages", "fitz");
  fs.mkdirSync(nested, { recursive: true });
  const binary = Buffer.alloc(8);
  binary.writeUInt32LE(0xcffaedfe, 0);
  fs.writeFileSync(path.join(nested, "_mupdf.so"), binary);
  fs.writeFileSync(path.join(root, "bin-note.txt"), "not a binary");
  const outside = path.join(os.tmpdir(), `osa-sign-outside-${Date.now()}`);
  fs.writeFileSync(outside, binary);
  fs.symlinkSync(outside, path.join(root, "escape"));

  const selected = signer.machOPaths(root);

  assert.deepEqual(selected, [path.join(nested, "_mupdf.so")]);
  fs.unlinkSync(outside);
});
