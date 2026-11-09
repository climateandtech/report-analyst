"use strict";

const assert = require("node:assert/strict");
const fs = require("fs");
const path = require("path");
const test = require("node:test");

test("packaged files include the window icon used by main.js", () => {
  const packageJson = JSON.parse(fs.readFileSync(path.join(__dirname, "package.json"), "utf8"));
  assert.ok(packageJson.build.files.includes("build/icon.png"));
  assert.ok(fs.existsSync(path.join(__dirname, "build", "icon.png")));
});

test("main.js tolerates a missing icon path", () => {
  const source = fs.readFileSync(path.join(__dirname, "main.js"), "utf8");
  assert.match(source, /function appIconPath\(/);
  assert.match(source, /\.\.\.\(iconPath \? \{ icon: iconPath \} : \{\}\)/);
});
